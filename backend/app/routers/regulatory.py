from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import RegulatoryAlert, RegulatoryUpdate
from app.services.regulatory_scraper import regulatory_scraper

router = APIRouter(prefix="/api/v1/regulatory", tags=["regulatory"])

@router.get("/alerts")
async def list_alerts(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(RegulatoryAlert).where(RegulatoryAlert.org_id == org_id).order_by(RegulatoryAlert.created_at.desc())
    )
    alerts = result.scalars().all()
    return [a.model_dump() for a in alerts]

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RegulatoryAlert).where(RegulatoryAlert.id == alert_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    a.status = "acknowledged"
    await session.commit()
    return {"status": "acknowledged"}

@router.get("/alerts/unread-count")
async def unread_count(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(RegulatoryAlert).where(RegulatoryAlert.org_id == org_id, RegulatoryAlert.status == "unread")
    )
    count = len(result.scalars().all())
    return {"count": count}

@router.get("/updates")
async def list_updates(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RegulatoryUpdate).order_by(RegulatoryUpdate.created_at.desc()))
    updates = result.scalars().all()
    return [u.model_dump() for u in updates]

@router.get("/dashboard")
async def regulatory_dashboard(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(RegulatoryAlert).where(RegulatoryAlert.org_id == org_id))
    alerts = result.scalars().all()
    unread = len([a for a in alerts if a.status == "unread"])
    by_priority = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for a in alerts:
        if a.priority in by_priority:
            by_priority[a.priority] += 1
    return {"total_alerts": len(alerts), "unread": unread, "by_priority": by_priority}

@router.post("/scrape")
async def scrape_regulatory(background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    result = await regulatory_scraper.scrape_all(session)
    return {"status": "completed", **result}
