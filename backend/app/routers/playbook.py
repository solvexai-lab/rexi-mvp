from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import PlaybookRule

router = APIRouter(prefix="/api/v1/playbook", tags=["playbook"])

@router.get("/rules")
async def list_rules(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlaybookRule).where(PlaybookRule.org_id == org_id))
    rules = result.scalars().all()
    return [r.model_dump() for r in rules]

@router.post("/rules")
async def create_rule(rule: PlaybookRule, session: AsyncSession = Depends(get_session)):
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule.model_dump()

@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, rule: PlaybookRule, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlaybookRule).where(PlaybookRule.id == rule_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")
    existing.rule_name = rule.rule_name
    existing.rule_type = rule.rule_type
    existing.condition = rule.condition
    existing.threshold_value = rule.threshold_value
    existing.severity = rule.severity
    existing.is_active = rule.is_active
    await session.commit()
    await session.refresh(existing)
    return existing.model_dump()

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlaybookRule).where(PlaybookRule.id == rule_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(r)
    await session.commit()
    return {"status": "deleted"}
