# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import weaviate
import os
from utils import fetch_html, extract_text_chunks, embed_texts
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = Flask(__name__)
CORS(app)

WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
client = weaviate.Client(url=WEAVIATE_URL)

# ensure schema
def ensure_schema():
    class_name = "HtmlChunk"
    if client.schema.contains({"class": class_name}):
        return
    schema = {
        "class": class_name,
        "vectorizer": "none",
        "properties": [
            {"name": "url", "dataType": ["string"]},
            {"name": "path", "dataType": ["string"]},
            {"name": "chunk_text", "dataType": ["text"]},
            {"name": "chunk_html", "dataType": ["text"]},
        ],
    }
    client.schema.create_class(schema)

ensure_schema()

# re-ranker model (HF transformers)
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
device = "cuda" if torch.cuda.is_available() else "cpu"
RE_TOKENIZER = AutoTokenizer.from_pretrained(RERANKER_MODEL)
RE_MODEL = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL).to(device)
RE_MODEL.eval()

def rerank_with_transformers(query, candidate_texts, batch_size=16):
    scores = []
    for i in range(0, len(candidate_texts), batch_size):
        batch = candidate_texts[i:i+batch_size]
        enc = RE_TOKENIZER([query]*len(batch), batch, padding=True, truncation=True, return_tensors="pt").to(device)
        with torch.no_grad():
            out = RE_MODEL(**enc)
            logits = out.logits
            if logits.shape[1] == 1:
                vals = logits[:,0].cpu().numpy().tolist()
            else:
                probs = torch.softmax(logits, dim=1)
                vals = probs[:,1].cpu().numpy().tolist()
            scores.extend(vals)
    return scores

@app.route("/ingest", methods=["POST"])
def ingest():
    payload = request.get_json()
    url = payload.get("url")
    if not url:
        return {"error": "url required"}, 400

    html = fetch_html(url)
    chunks = extract_text_chunks(html, max_chunk_tokens=500)
    if not chunks:
        return {"error":"no chunks"}, 400

    texts = [c["text"] for c in chunks]
    embs = embed_texts(texts)  # normalized vectors

    batch = client.batch
    batch.batch_size = 50
    for c, vec in zip(chunks, embs):
        properties = {
            "url": url,
            "path": c.get("path", "/"),
            "chunk_text": c["text"],
            "chunk_html": c.get("html", "")
        }
        batch.add_data_object(properties, "HtmlChunk", vector=vec.tolist())
    batch.flush()
    return {"status":"ok","indexed":len(chunks)}

@app.route("/search", methods=["POST"])
def search():
    payload = request.get_json()
    query = payload.get("query")
    k = int(payload.get("k", 10))
    if not query:
        return {"error":"query required"}, 400

    bi = SentenceTransformer("all-mpnet-base-v2")
    q_emb = bi.encode([query], convert_to_numpy=True).astype("float32")
    q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)

    response = (
        client.query
        .get("HtmlChunk", ["url", "path", "chunk_text", "chunk_html"])
        .with_near_vector({"vector": q_emb[0].tolist()})
        .with_limit(max(50, k*5))
        .do()
    )

    raw_hits = response.get("data", {}).get("Get", {}).get("HtmlChunk", [])
    if not raw_hits:
        return {"results": []}

    candidate_texts = [h.get("chunk_text","") for h in raw_hits]
    rerank_scores = rerank_with_transformers(query, candidate_texts)
    candidates = list(zip(raw_hits, rerank_scores))
    candidates.sort(key=lambda x: x[1], reverse=True)
    top = candidates[:k]

    scores_only = [s for (_, s) in top] if top else [0.0]
    min_s = min(scores_only)
    max_s = max(scores_only)
    rng = max_s - min_s if max_s > min_s else 1.0

    results = []
    for hit, raw_score in top:
        pct = max(0.0, min(1.0, (raw_score - min_s)/rng)) * 100.0
        results.append({
            "text": hit.get("chunk_text",""),
            "html": hit.get("chunk_html",""),
            "path": hit.get("path","/"),
            "url": hit.get("url"),
            "score": round(pct,2)
        })

    return {"results": results}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
