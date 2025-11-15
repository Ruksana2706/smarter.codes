Weaviate Fullstack Semantic Search

Steps to run (local machine):

1) Install Docker (Docker Desktop) and make sure docker is running.

2) Start Weaviate:
   docker compose up -d
   Wait until ready:
   curl http://localhost:8080/v1/.well-known/ready

3) Backend:
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   (on Windows use .venv\Scripts\activate)
   pip install --upgrade pip
   pip install -r requirements.txt
   python app.py

   Note: First run will download sentence-transformers and the re-ranker model (may be 200-500MB).

4) Frontend:
   cd frontend
   npm install
   npm start
   Open http://localhost:3000

How it works:
- Use the frontend form to input a Website URL and a Search Query.
- When searching, the frontend calls /ingest to fetch & index the URL (if provided) then /search to get top matches.
- Results show match % and View HTML for the raw snippet.

Troubleshooting:
- If pip install of faiss-cpu fails on your platform, install faiss from conda or use a CPU-compatible wheel. Alternatively remove faiss and use the Weaviate-only pipeline (we already use Weaviate for retrieval).
- If transformers/torch installation is slow, be patient; these are large packages.
