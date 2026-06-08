"""REXI API — PostgreSQL + Auth + Audit."""
# Load .env before any imports that read environment variables
from dotenv import load_dotenv
load_dotenv()

# Bootstrap vendor repos into Python path FIRST
from app.core.vendor_bootstrap import bootstrap
bootstrap()

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import select

# Import all table models so SQLModel registers them
from app.models.tables import (
    User, Organization, Contract, ContractClause, ContractVersion,
    PlainEnglishSummary, ClauseHighlight, ContractEmbedding,
    Obligation, PlaybookRule,
    EnforceabilityBenchmark, RegulatorySource, RegulatoryUpdate,
    RegulatoryAlert, ContractTemplate, ApprovalStage, ContractComment,
    Notification, AutomationLog, AuditTrailEntry, ContractTreeIndex,
)
from app.core.database import init_db, health_check
from app.core.seed import seed_database
from app.routers import (
    contracts, playbook, regulatory, knowledge_graph, network_graph,
    obligations, templates, audit, approvals, comments,
    notifications, reports, analytics, admin, organizations,
    plain_english, redline, chat, highlights, counterparty,
    embeddings, docx_diff, fingerprint, pii, pageindex,
)


import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables immediately, seed in background. Shutdown: cleanup."""
    print("[STARTUP] Initializing database...")
    try:
        await init_db()
        print("[STARTUP] Database initialized OK")
    except Exception as e:
        print(f"[STARTUP] Database init FAILED: {e}")
    print("[STARTUP] Starting background seed...")
    try:
        asyncio.create_task(seed_database())
        print("[STARTUP] Background seed started")
    except Exception as e:
        print(f"[STARTUP] Background seed FAILED: {e}")
    print("[STARTUP] App ready — binding to port")
    try:
        yield
    finally:
        pass


app = FastAPI(title="REXI API", version="2.0", lifespan=lifespan)

# CORS — configurable via env var. When serving frontend from same origin, CORS is not needed.
_cors_raw = os.getenv("CORS_ORIGINS", "")
if _cors_raw.strip():
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
else:
    _cors_origins = [
        "http://localhost:5173", "http://localhost:3000",
        "http://127.0.0.1:5173", "http://127.0.0.1:3000",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(contracts.router)
app.include_router(playbook.router)
app.include_router(regulatory.router)
app.include_router(network_graph.router)
app.include_router(knowledge_graph.router)
app.include_router(obligations.router)
app.include_router(templates.router)
app.include_router(audit.router)
app.include_router(approvals.router)
app.include_router(comments.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(organizations.router)
app.include_router(plain_english.router)
app.include_router(redline.router)
app.include_router(chat.router)
app.include_router(highlights.router)
app.include_router(counterparty.router)
app.include_router(embeddings.router)
app.include_router(docx_diff.router)
app.include_router(fingerprint.router)
app.include_router(pii.router)
app.include_router(pageindex.router)

@app.get("/health")
async def health():
    db_ok = await health_check()
    return {"status": "ok" if db_ok else "degraded", "version": "2.0", "database": "connected" if db_ok else "disconnected"}


# Serve built frontend static files if present (production / single-container deploy).
# MUST be registered after all API routes so that API paths take precedence.
_static_dir = os.getenv("FRONTEND_DIST_DIR", "")
if not _static_dir:
    # Try common relative paths (local dev vs Docker)
    _base = os.path.dirname(__file__)
    for _candidate in [os.path.join(_base, "../frontend/dist"), os.path.join(_base, "../../frontend/dist")]:
        if os.path.isdir(_candidate) and os.path.exists(os.path.join(_candidate, "index.html")):
            _static_dir = _candidate
            break
if _static_dir and os.path.isdir(_static_dir) and os.path.exists(os.path.join(_static_dir, "index.html")):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
