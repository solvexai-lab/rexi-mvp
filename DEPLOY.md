# REXI Deployment Guide

## Quick Start — Single Container (Recommended for Demos)

Build and run everything in one Docker container:

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY and DATABASE_URL

# 2. Build and run
docker compose -f docker-compose.prod.yml up --build -d

# 3. Open http://localhost:8000
```

This serves the React frontend **and** FastAPI backend on a single port (`8000`).
No CORS. No separate frontend server. One URL, one container.

---

## Architecture

```
┌─────────────────────────────────────────┐
│           Docker Host                   │
│  ┌─────────────────────────────────┐    │
│  │  REXI Container (port 8000)     │    │
│  │  ├── FastAPI API  /api/v1/...   │    │
│  │  ├── Health       /health       │    │
│  │  └── React SPA    /*            │    │
│  └─────────────────────────────────┘    │
│              │                          │
│  ┌───────────┴───────────────────┐      │
│  │  PostgreSQL (port 5432)       │      │
│  └───────────────────────────────┘      │
└─────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `SECRET_KEY` | Yes | `rexi-super-secret...` | JWT / session secret |
| `CORS_ORIGINS` | No | `localhost:*` | Comma-separated allowed origins |
| `NEO4J_URI` | No | — | Optional Knowledge Graph |
| `MINIO_ENDPOINT` | No | — | Optional S3-compatible storage |
| `UPLOAD_DIR` | No | `./uploads` | Local file upload path |

---

## Deployment Options

### Option A: Docker Compose on a VPS (Easiest)

```bash
# On any Linux server with Docker
git clone <repo>
cd rexi-mvp
cp .env.example .env
# Edit .env with your keys

docker compose -f docker-compose.prod.yml up --build -d
```

Access at `http://<server-ip>:8000`

### Option B: Railway / Render / Fly.io

1. Set environment variables in the platform dashboard
2. Use the root `Dockerfile` (multi-stage build)
3. Expose port `8000`
4. Platform handles HTTPS → no CORS needed

### Option C: Separate Frontend + Backend

If you prefer separate services:

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
# Serve `dist/` with nginx, Vercel, Netlify, or S3
```

Set `VITE_API_URL=https://your-backend-url/api/v1` before building.

---

## Cloud Database (Neon)

The included `docker-compose.prod.yml` spins up a local PostgreSQL.
For persistent cloud hosting, replace `DATABASE_URL` with a Neon connection string:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx-pooler.c-7.us-east-1.aws.neon.tech/db?sslmode=require
```

Then remove the `postgres` service from `docker-compose.prod.yml`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 8000 in use | Change `ports:` in `docker-compose.prod.yml` to `"8001:8000"` |
| Frontend shows blank | Check browser console for 404s on `/assets/` — ensure `npm run build` succeeded |
| API calls fail with CORS | Set `CORS_ORIGINS=https://your-domain.com` in `.env` |
| Gemini not responding | Verify `GEMINI_API_KEY` is set and has quota |
| File uploads disappear | Mount a persistent volume for `/app/uploads` |

---

## Local Development

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173`, proxied to backend on `8001`.
