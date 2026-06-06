from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import Notification

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("")
async def list_notifications(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Notification).where(Notification.org_id == org_id).order_by(Notification.created_at.desc())
    )
    notifications = result.scalars().all()
    return [n.model_dump() for n in notifications]

@router.get("/unread-count")
async def unread_count(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Notification).where(Notification.org_id == org_id, Notification.is_read == False)
    )
    count = len(result.scalars().all())
    return {"count": count}

@router.put("/{notification_id}/read")
async def mark_read(notification_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Notification).where(Notification.id == notification_id))
    n = result.scalar_one_or_none()
    if n:
        n.is_read = True
        await session.commit()
        return {"status": "read"}
    raise HTTPException(status_code=404, detail="Not found")

@router.put("/read-all")
async def mark_all_read(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Notification).where(Notification.org_id == org_id, Notification.is_read == False))
    for n in result.scalars().all():
        n.is_read = True
    await session.commit()
    return {"status": "all_read"}
