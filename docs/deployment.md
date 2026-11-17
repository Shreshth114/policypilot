# Free Render deployment

This deployment runs the React website and FastAPI API in one Docker web service.
`render.yaml` explicitly selects the Free instance type and provisions no paid
database, disk, or other service.

1. Push this repository to a GitHub repository you control.
2. In Render, create a **Blueprint** and select that repository.
3. Confirm the web service instance type is **Free**.
4. Enter `GROQ_API_KEY` when prompted, then deploy.
5. Open the resulting `https://...onrender.com` address. Check `/api/health` and
   confirm the policy library contains both bundled documents.

Never commit `.env` or put API keys in frontend build variables. The Docker build
excludes local environment files and databases. Render injects the Groq key into
the backend at runtime.

## Free-tier behavior

- The app sleeps when idle; the next request can take time to start.
- SQLite lives in `/tmp/policypilot`. Data can reset on restart or deployment.
- Both tracked PDFs under `backend/storage/pdfs` are indexed automatically at
  startup. SHA-256 deduplication makes repeat startup safe.
- Uploads, deletions, chat, search, and retrieval benchmarks are all available.
  The prototype has no admin authentication; catalog changes are available to
  anyone visiting the website. Benchmarks use the provider's free-tier quota.
- Groq free-tier quotas still apply. The existing offline fallback is used if the
  provider cannot answer. This setup is for a small demonstration, with one server
  instance and no persistent user-data guarantee.

## Local verification

```sh
python3 -m venv backend/venv
backend/venv/bin/python -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
PYTHONPATH=backend SEED_POLICIES=true STORAGE_DIR=/tmp/policypilot DATABASE_URL=sqlite:////tmp/policypilot/policypilot.db backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The frontend uses relative `/api` requests. Vite proxies them during development;
FastAPI serves the built website in deployment. A separate frontend host can set
`VITE_API_BASE_URL` at build time.
