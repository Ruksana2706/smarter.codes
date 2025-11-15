# backend/utils.py
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
import numpy as np
import re

# Bi-encoder model for vector embeddings (higher quality)
EMB_MODEL_NAME = "all-mpnet-base-v2"
EMB_MODEL = SentenceTransformer(EMB_MODEL_NAME)

TOKENIZER = AutoTokenizer.from_pretrained("bert-base-uncased")
_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

def fetch_html(url, timeout=10):
    resp = requests.get(url, timeout=timeout, headers={"User-Agent":"html-search-bot/1.0"})
    resp.raise_for_status()
    return resp.text

def clean_text(t: str):
    return re.sub(r'\s+', ' ', t).strip()

def split_sentences(text):
    parts = _SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]

def element_path(el):
    tag = el.name or "elem"
    id_attr = el.get("id")
    cls = el.get("class")
    cls_str = ""
    if cls:
        cls_str = "." + ".".join(cls)
    if id_attr:
        return f"{tag}#{id_attr}{cls_str}"
    return f"{tag}{cls_str}"

def extract_text_chunks(html, max_chunk_tokens=500):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript","head","footer","nav","svg","iframe"]):
        tag.decompose()

    blocks = []
    for tag in soup.find_all(["article","section","main","div","p","li","h1","h2","h3","h4"]):
        try:
            raw_html = tag.decode_contents()
        except Exception:
            raw_html = tag.get_text(separator=" ", strip=True)
        text = clean_text(tag.get_text(separator=" ", strip=True))
        if len(text) > 40:
            blocks.append((text, raw_html, element_path(tag)))

    if not blocks:
        body_text = clean_text(soup.get_text(" ", strip=True))
        body_html = soup.body.decode_contents() if soup.body else ""
        blocks = [(body_text, body_html, "/")]

    chunks = []
    current_text = ""
    current_html_parts = []
    current_path = "/"

    for (block_text, block_html, block_path) in blocks:
        sents = split_sentences(block_text)
        for s in sents:
            if not s:
                continue
            candidate = (current_text + " " + s).strip() if current_text else s
            token_count = len(TOKENIZER.tokenize(candidate))
            if token_count <= max_chunk_tokens:
                current_text = candidate
                if block_html:
                    current_html_parts.append(block_html)
                current_path = current_path if current_path != "/" else block_path
            else:
                if current_text:
                    html_snippet = current_html_parts[-1] if current_html_parts else block_html
                    chunks.append({
                        "text": current_text,
                        "html": html_snippet,
                        "path": current_path
                    })
                if len(TOKENIZER.tokenize(s)) > max_chunk_tokens:
                    words = s.split()
                    part = ""
                    for w in words:
                        cand = (part + " " + w).strip() if part else w
                        if len(TOKENIZER.tokenize(cand)) <= max_chunk_tokens:
                            part = cand
                        else:
                            chunks.append({
                                "text": part,
                                "html": block_html,
                                "path": block_path
                            })
                            part = w
                    if part:
                        chunks.append({
                            "text": part,
                            "html": block_html,
                            "path": block_path
                        })
                    current_text = ""
                    current_html_parts = []
                    current_path = "/"
                else:
                    current_text = s
                    current_html_parts = [block_html] if block_html else []
                    current_path = block_path

    if current_text:
        html_snippet = current_html_parts[-1] if current_html_parts else ""
        chunks.append({
            "text": current_text,
            "html": html_snippet,
            "path": current_path
        })

    # dedupe by prefix
    seen = set()
    final = []
    for c in chunks:
        key = c["text"][:200].lower()
        if key not in seen:
            seen.add(key)
            final.append(c)
    return final

def embed_texts(texts, model=EMB_MODEL):
    embs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embs = embs / norms
    return embs.astype("float32")
