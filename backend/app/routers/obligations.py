from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import Obligation

router = APIRouter(prefix="/api/v1/obligations", tags=["obligations"])

@router.get("")
async def list_obligations(org_id: str = "demo-org", filter_status: Optional[str] = None, session: AsyncSession = Depends(get_session)):
    query = select(Obligation).where(Obligation.org_id == org_id)
    if filter_status:
        query = query.where(Obligation.status == filter_status)
    result = await session.execute(query)
    obligations = result.scalars().all()
    return [o.model_dump() for o in obligations]

@router.post("")
async def create_obligation(obligation: Obligation, session: AsyncSession = Depends(get_session)):
    session.add(obligation)
    await session.commit()
    await session.refresh(obligation)
    return obligation.model_dump()

@router.get("/{obligation_id}")
async def get_obligation(obligation_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Obligation).where(Obligation.id == obligation_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    return o.model_dump()

@router.put("/{obligation_id}/status")
async def update_obligation_status(obligation_id: str, status: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Obligation).where(Obligation.id == obligation_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    o.status = status
    await session.commit()
    await session.refresh(o)
    return o.model_dump()

@router.delete("/{obligation_id}")
async def delete_obligation(obligation_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Obligation).where(Obligation.id == obligation_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(o)
    await session.commit()
    return {"status": "deleted"}

@router.get("/dashboard/summary")
async def obligations_dashboard(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Obligation).where(Obligation.org_id == org_id))
    obligations = result.scalars().all()
    total = len(obligations)
    pending = sum(1 for o in obligations if o.status == "pending")
    completed = sum(1 for o in obligations if o.status == "completed")
    overdue = sum(1 for o in obligations if o.status == "overdue")
    return {"total": total, "pending": pending, "completed": completed, "overdue": overdue}
