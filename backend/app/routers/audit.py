from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import AutomationLog, AuditTrailEntry
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

@router.get("/logs")
async def list_logs(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AutomationLog).where(AutomationLog.org_id == org_id).order_by(AutomationLog.created_at.desc())
    )
    logs = result.scalars().all()
    return [l.model_dump() for l in logs]

@router.get("/logs/recent")
async def recent_logs(org_id: str = "demo-org", limit: int = 10, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AutomationLog)
        .where(AutomationLog.org_id == org_id)
        .order_by(AutomationLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [l.model_dump() for l in logs]

# ---------------------------------------------------------------------------
# Tamper-proof audit trail
# ---------------------------------------------------------------------------
@router.get("/trail")
async def get_audit_trail(
    org_id: str = "demo-org",
    resource_type: str = None,
    resource_id: str = None,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    entries = await audit_service.get_trail(session, org_id, resource_type, resource_id, limit)
    return [e.model_dump() for e in entries]

@router.post("/trail/verify")
async def verify_audit_chain(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await audit_service.verify_chain(session, org_id)
    return result
