# smarter.codes
A full-stack semantic search tool that extracts website content, converts it into vector embeddings, stores it in Weaviate, and returns highly relevant results using cross-encoder reranking. Built with Flask and React, featuring HTML previews and match scoring.

Website Content Search Engine
Search any website semantically using ML embeddings, vector database (Weaviate), and
cross-encoder reranking.
Features:
- Extract HTML content from any webpage
- Convert into semantic chunks (max 500 tokens)
- Store chunks in Weaviate vector database
- Embed using SentenceTransformer (all-mpnet-base-v2)
- Search using semantic similarity
- Rerank using cross-encoder (ms-marco MiniLM)
- Frontend shows match %, text preview, path, and HTML

Setup and Start
Prerequisites:
- Python 3.10+
- React.js + npm
- Docker Desktop
- 8 GB RAM recommended

Instructions:
1. Start Weaviate:
docker compose up -d
curl http://localhost:8080/v1/.well-known/ready

2. Backend Setup:
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py

3. Frontend Setup:
cd frontend
npm install
npm start

4. Use:
- Enter Website URL
- Enter Search Query
- Click Search
- View semantic match %, preview, and HTML snippet.
