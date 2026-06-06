"""REXI API — PostgreSQL + Auth + Audit."""
# Bootstrap vendor repos into Python path FIRST
from app.core.vendor_bootstrap import bootstrap
bootstrap()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

# Import all table models so SQLModel registers them
from app.models.tables import (
    User, Organization, Contract, ContractClause, ContractVersion,
    PlainEnglishSummary, ClauseHighlight, ContractEmbedding,
    Obligation, PlaybookRule, RiskAssessment, RiskFinding,
    EnforceabilityBenchmark, RegulatorySource, RegulatoryUpdate,
    RegulatoryAlert, ContractTemplate, ApprovalStage, ContractComment,
    Notification, AutomationLog, AuditTrailEntry, ContractTreeIndex,
)
from app.core.database import init_db, health_check
from app.core.seed import seed_database
from app.routers import (
    contracts, risk, playbook, regulatory, knowledge_graph, network_graph,
    obligations, templates, audit, approvals, comments,
    notifications, reports, analytics, admin, organizations,
    plain_english, redline, chat, highlights, counterparty,
    embeddings, docx_diff, fingerprint, pii, pageindex,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed. Shutdown: cleanup."""
    await init_db()
    await seed_database()
    try:
        yield
    finally:
        pass


app = FastAPI(title="REXI API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(contracts.router)
app.include_router(risk.router)
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
