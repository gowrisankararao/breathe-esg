# Breathe ESG — Data Ingestion & Review Prototype

Django REST + React prototype for ingesting SAP, utility, and corporate travel data, normalizing it for GHG reporting, and letting analysts review before audit lock.

## Quick start (local)

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — login: **analyst** / **demo1234**

Sample files are in `sample_data/`.

## Deploy (Render)

1. Push to GitHub and connect repo on [Render](https://render.com).
2. Use the `render.yaml` blueprint (Web Service + PostgreSQL).
3. Set `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to your Render URL (e.g. `https://breathe-esg.onrender.com`).
4. After deploy, log in with analyst / demo1234 (created by `seed_demo`).

## Documentation

| File | Purpose |
|------|---------|
| [MODEL.md](MODEL.md) | Data model, multi-tenancy, audit trail |
| [DECISIONS.md](DECISIONS.md) | Ambiguities resolved and PM questions |
| [TRADEOFFS.md](TRADEOFFS.md) | Three deliberate omissions |
| [SOURCES.md](SOURCES.md) | Real-world format research per source |

## Architecture

```
sample_data/*.csv  →  upload API  →  parsers  →  ActivityRecord
                                              →  RawRecord (staging)
                                              →  AuditLog
                         ↓
              React review dashboard (approve / reject / lock)
```
