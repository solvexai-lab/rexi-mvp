# REXI MVP — Agent Guide

This document contains everything an AI coding agent needs to know to work effectively on the REXI MVP codebase.

---

## Project Overview

REXI MVP is a pre-seed legal tech platform for India's mid-market. It integrates three pillars into a single web application:

1. **CLM (Contract Lifecycle Management)** — PDF upload, clause extraction, obligation tracking, approval workflows, templates, comments.
2. **AI Risk Assessment** — 3-layer scoring: Playbook rules (35%), Indian law benchmarks (40%), Regulatory gaps (25%).
3. **Regulatory Intelligence** — RSS scraping from RBI/SEBI/MCA/Labour Ministry, auto-alerts, impact analysis.

The backend is a Python FastAPI application with a PostgreSQL database and an optional Neo4j Knowledge Graph. The frontend is a React 18 + Vite SPA.

All comments and documentation in the project are in English. Write code, comments, and documentation in English.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite 5, Tailwind CSS 3, Lucide React, Recharts, vis-network, react-pdf, Framer Motion, TanStack Query |
| Backend | Python 3.11, FastAPI, Pydantic v2, Uvicorn, SQLModel (SQLAlchemy 2.0 + Pydantic), asyncpg |
| Auth | fastapi-users with JWT bearer transport, bcrypt/passlib, python-jose |
| Document Processing | Docling (primary, IBM/MIT license), PyMuPDF (fallback), pdfplumber (tables/highlights) |
| AI / LLM | Google Gemini (`gemini-2.0-flash`) via `google-generativeai`, OpenAI GPT-4o-mini for clause extraction fallback |
| Embeddings | OpenAI embeddings, Gemini embeddings, or a `HashEmbedder` fallback |
| Graph DB | Neo4j 5.15 Community (APOC + GDS plugins). Optional — features degrade gracefully if unavailable |
| Relational DB | PostgreSQL 15+ (local or Neon). CI uses Postgres 16. Backend tests use aiosqlite in-memory |
| Object Storage | MinIO (S3-compatible). Falls back to local filesystem if unavailable |
| PII Detection | Microsoft Presidio + custom regex for Indian IDs (PAN, GSTIN, Aadhaar, IFSC, UPI) |
| Observability | Optional Langfuse integration (zero-overhead no-op when not configured) |

**Important licensing note:** The `vendor/marker/` directory exists for reference only. Marker model weights are under CC-BY-NC-SA (non-commercial), so REXI uses Docling instead.

---

## Directory Structure

```
rexi-mvp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory, lifespan, router registration
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings (.env loader)
│   │   │   ├── database.py      # Async SQLAlchemy engine/session, init_db, health_check
│   │   │   ├── auth.py          # fastapi-users JWT setup
│   │   │   ├── seed.py          # 1,200+ line seeder with 4 demo contracts, rules, benchmarks, alerts
│   │   │   ├── vendor_bootstrap.py  # Injects vendor/ repos into sys.path at startup
│   │   │   └── pdf_generator.py # PDF generation utility
│   │   ├── models/
│   │   │   └── tables.py        # 23 SQLModel table definitions
│   │   ├── routers/             # 26 API route modules (see list below)
│   │   └── services/            # 20+ business-logic services
│   ├── tests/                   # pytest test suite (9 files, ~1,500 lines)
│   ├── requirements.txt         # Python dependencies (no pyproject.toml)
│   └── pytest.ini               # pytest configuration
├── frontend/
│   ├── src/
│   │   ├── main.tsx             # Entry point
│   │   ├── App.tsx              # Root layout, sidebar, routing
│   │   ├── pages/               # 16 route-level pages
│   │   ├── components/          # Shared reusable components
│   │   ├── hooks/
│   │   │   ├── useQueries.ts    # 40+ TanStack Query hooks
│   │   │   └── useToast.ts      # Toast wrappers
│   │   └── lib/
│   │       ├── api.ts           # Thin fetch client with retry logic
│   │       └── queryClient.ts   # QueryClient config
│   ├── package.json             # Node dependencies (no test runner installed)
│   ├── vite.config.ts           # Vite config with proxy and manual chunks
│   ├── tailwind.config.js       # Custom theme colors
│   └── tsconfig.json            # TypeScript config
├── vendor/                      # 11 research/reference submodules (read-only reference)
├── docker-compose.yml           # Postgres, Neo4j, MinIO, backend, frontend
├── start.sh                     # Docker Compose startup script
├── run_servers.py               # Windows-only background process launcher
└── .github/workflows/ci.yml     # GitHub Actions CI
```

### Backend Routers (26 modules)

Registered in `app/main.py` without explicit prefixes (prefixes are defined inside each router module):

- `contracts` — Upload, list, get, delete, update, assess, serve PDF
- `risk` — Dashboard, findings, resolve
- `playbook` — CRUD for company playbook rules
- `regulatory` — Sources, updates, alerts, scrape trigger
- `knowledge_graph` — 3-Pillar Impact Engine (SQL-first + optional Neo4j)
- `network_graph` — Visual network graph data
- `obligations` — Contract & org-wide obligations tracking
- `templates` — Contract template CRUD with variable substitution
- `audit` — Immutable hashed audit trail
- `approvals` — Multi-stage approval workflow
- `comments` — Clause-level comments
- `notifications` — In-app notification feed
- `reports` — Compliance/risk report generation
- `analytics` — Dashboard metrics & charts data
- `admin` — Admin endpoints
- `organizations` — Org CRUD
- `plain_english` — Translate clauses to plain English via Gemini
- `redline` — Track-changes generation between versions
- `chat` — RAG chat with contracts (non-streaming + SSE streaming)
- `highlights` — PDF bounding-box highlights
- `counterparty` — Counterparty risk analysis
- `embeddings` — Clause vector indexing and semantic search
- `docx_diff` — DOCX diff generation
- `fingerprint` — Contract deduplication (MinHash + Jaccard)
- `pii` — PII analyze/anonymize/validate/scan
- `pageindex` — Hierarchical document tree retrieval
- `auth` (fastapi-users) — Register, login, JWT, password reset

---

## Build and Run Commands

### Docker Compose (recommended)

```bash
# Start everything
./start.sh

# Or manually
docker compose up -d neo4j minio
sleep 10
docker compose up -d backend frontend
```

Services:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs (Swagger UI): http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474 (neo4j / rexi_neo4j_2025)
- MinIO Console: http://localhost:9001 (rexi_minio / rexi_minio_secret)

### Local Backend (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Local Frontend (without Docker)

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

### Production Build

```bash
cd frontend
npm run build          # Outputs to frontend/dist/
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`run_servers.py` is a Windows-specific script that starts backend and serves `frontend/dist/` via Python's `http.server` as background processes.

---

## Testing Instructions

### Backend Tests

```bash
cd backend
pytest -v --cov=app --cov-report=term-missing
```

- Uses `sqlite+aiosqlite:///:memory:` automatically via `conftest.py`.
- No external DB needed for local test runs.
- Some tests skip when `GEMINI_API_KEY` is missing.

**Test database setup (`tests/conftest.py`):**
- Session-scoped fixture creates all tables via `SQLModel.metadata`.
- Per-test fixture truncates all tables for isolation.
- Overrides `get_session` dependency globally.
- Provides `client` (httpx.AsyncClient with ASGITransport) and `db_session`.

**Testing strategy:** Heavy use of `unittest.mock` (AsyncMock, MagicMock, patch) to avoid loading large ML models (Marker, Presidio, Langfuse, deepeval) — keeps CI fast.

### Frontend Tests

There are **no frontend unit tests** currently. No test runner (Jest/Vitest) is installed. The CI runs lint and type-check steps with `|| true` fallbacks.

### CI/CD (GitHub Actions)

File: `.github/workflows/ci.yml`

**Backend job:**
1. Installs dependencies from `requirements.txt`
2. Lint: `ruff check app tests` + `ruff format --check app tests`
3. Type check: `mypy app --ignore-missing-imports`
4. Test: `pytest -v --cov=app --cov-report=term-missing` against Postgres 16 service container

**Frontend job:**
1. `npm ci`
2. `npm run lint || true`
3. `npm run type-check || npx tsc --noEmit`
4. `npm run build`

Triggers: push/PR to `main` or `develop`.

---

## Code Style Guidelines

### Python (Backend)

- **Formatter/Linter:** Ruff (used in CI; no project-level config file — defaults apply).
- **Type checker:** mypy (`mypy app --ignore-missing-imports`).
- **Import style:** Absolute imports within `app/`. `vendor_bootstrap.py` injects `vendor/` repos into `sys.path` at startup so they can be imported directly.
- **Async everywhere:** The backend is fully async — use `async`/`await` for DB operations, HTTP calls, and external API calls.
- **ORM:** SQLModel. Table definitions go in `app/models/tables.py`. All models must be imported in `app/main.py` so SQLModel registers them.
- **Graceful degradation:** Every external dependency must fail safely:
  - Docling → PyMuPDF fallback for PDF processing
  - Gemini → fallback response or rule-based logic
  - Neo4j → no-op / silent skip
  - MinIO → local filesystem fallback
  - Presidio → regex patterns fallback
  - Langfuse → zero-overhead no-op

### TypeScript / React (Frontend)

- **No ESLint or Prettier config** exists. TypeScript compiler is the primary quality gate.
- **Styling:** Tailwind CSS only. No shadcn, MUI, or AntD. Custom theme colors are defined in `tailwind.config.js`.
- **State management:** TanStack Query for all server state. Plain React `useState` for local UI state. No Redux, Zustand, or Context API for global state.
- **API calls:** All data fetching goes through `lib/api.ts` (thin fetch wrapper with retry) and `hooks/useQueries.ts`.
- **Organization scoping:** Almost every endpoint appends `?org_id=${ORG_ID}` where `ORG_ID` is read from `localStorage.getItem('rexi_org_id') || 'demo-org'`.
- **Routing:** `react-router-dom` v6. Routes are defined in `App.tsx` inside `AnimatePresence` for page transitions.

---

## Key Conventions and Patterns

### Database

- **No Alembic migrations.** Schema is created automatically at startup via `SQLModel.metadata.create_all()` inside `init_db()`.
- Neon PostgreSQL compatibility: `database.py` parses `sslmode` and builds proper TLS context for `.neon.tech` hosts.
- Engine pool config: size 5, max_overflow 5, pool_pre_ping, recycle 300s.

### 4-Phase Upload Pipeline (Contracts Router)

1. Short DB transaction to create contract record.
2. Heavy processing (PDF extraction, chunking, clause extraction) outside DB.
3. Persist results in a short DB transaction.
4. Non-blocking enrichment layers (PII scan, PageIndex tree, embeddings).

### "SQL-first, graph as view"

All deterministic business logic uses PostgreSQL/SQLModel. Neo4j is purely optional enrichment. The Knowledge Graph router provides SQL-first impact analysis with optional Neo4j visualization endpoints.

### Vendor Bootstrap

`app/core/vendor_bootstrap.py` adds `vendor/` subdirectories to `sys.path` at startup without pip-installing them. Any code that imports from `vendor/` modules relies on this bootstrap running first (it is imported at the very top of `app/main.py`).

### Auth Status

Auth infrastructure exists (fastapi-users tables, JWT backend, register/login endpoints), but the frontend currently operates in **"Demo Mode"** with no login wall. The org ID comes from `localStorage`. Full auth & multi-tenancy are planned for Q3.

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes | PostgreSQL async URL. Example: `postgresql+asyncpg://rexi:rexi_pass@localhost:5432/rexi_db` |
| `GEMINI_API_KEY` | Yes | Google Gemini API for Plain English, Chat, Explain Risk |
| `OPENAI_API_KEY` | No | GPT-4o-mini clause extraction fallback and OpenAI embeddings |
| `SECRET_KEY` | Yes | JWT signing key |
| `NEO4J_URI` | No | Optional. Example: `bolt://localhost:7687` |
| `NEO4J_USER` | No | Neo4j username |
| `NEO4J_PASSWORD` | No | Neo4j password |
| `UPLOAD_DIR` | No | Local file upload path. Default: `./uploads` |
| `MINIO_ENDPOINT` | No | MinIO/S3 endpoint. Falls back to local filesystem |
| `MINIO_ACCESS_KEY` | No | MinIO access key |
| `MINIO_SECRET_KEY` | No | MinIO secret key |

---

## Security Considerations

- CORS is currently configured with `allow_origins=["*"]` in `app/main.py`. Tighten this for production.
- `SECRET_KEY` defaults to a placeholder in `.env.example`. Change it to a cryptographically secure random string in production.
- Presidio and custom regex are used for PII detection and anonymization. The `pii` router supports Aadhaar, PAN, GSTIN, IFSC, UPI, and bank account validation for Indian documents.
- PDF processing downloads ~1GB of Docling models on first run. Verify model checksums if operating in a high-security environment.
- No rate limiting is currently implemented on API endpoints.
- All file uploads are stored either in MinIO or the local filesystem (`UPLOAD_DIR`). Ensure proper file permissions on the upload directory.

---

## Seeded Demo Data

On first startup, `app/core/seed.py` seeds:

- 1 Organization (Acme Manufacturing Pvt Ltd, `demo-org`)
- 4 full demo contracts with realistic Indian legal text (NDA, Vendor Supply, Employment, Software License)
- ~25 playbook rules across contract types
- 10 enforceability benchmarks (Indian Contract Act 1872, DPDP 2023, Arbitration Act 1996, Labour Codes, etc.)
- 10 regulatory updates (DPDP, Labour, RBI, SEBI, MCA, GST, etc.)
- 8 regulatory alerts mapped to affected contracts
- 4 contract templates with variable placeholders
- Pre-seeded obligations, automation logs, audit entries, and Neo4j statutes/regulations

---

## Useful References

- `README.md` — Human-facing project overview with architecture diagrams and API endpoint summary
- `PHASE3_PLAN.md` — Knowledge Graph 3-Pillar Architecture plan (Playbook / Law / Regulatory)
- `DEMO_SCRIPT.md` — 12–15 minute investor demo script with emergency fallbacks
- `FREE_POSTGRESQL_GUIDE.md` — Neon PostgreSQL setup guide
