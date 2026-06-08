"""Admin endpoints for demo seeding and maintenance."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session, async_session_factory
from app.core.seed import seed_database

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/seed")
async def run_seed(session: AsyncSession = Depends(get_session)):
    """Re-run database seeding. Useful for resetting demo data."""
    await seed_database()
    return {"status": "seeded"}


@router.post("/reset-demo")
async def reset_demo(session: AsyncSession = Depends(get_session)):
    """Truncate user-uploaded data while keeping seeded config."""
    from sqlalchemy import text
    from app.models.tables import Contract, ContractClause, Obligation, ApprovalStage, ContractComment, Notification, AutomationLog, AuditTrailEntry

    tables = [
        AuditTrailEntry, AutomationLog, Notification, ContractComment,
        ApprovalStage, Obligation,
        ContractClause, Contract,
    ]
    for table in tables:
        await session.execute(text(f"DELETE FROM {table.__tablename__}"))
    await session.commit()
    await seed_database()
    return {"status": "reset"}
