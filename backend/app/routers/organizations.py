"""Organization profile endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import Organization

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.get("/{org_id}")
async def get_organization(org_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "id": org.id,
        "name": org.name,
        "industry": org.industry,
        "revenue_range": org.revenue_range,
        "employee_count": org.employee_count,
        "address": org.address,
        "gstin": org.gstin,
        "cin": org.cin,
        "dpo_name": org.dpo_name,
        "dpo_email": org.dpo_email,
    }


@router.put("/{org_id}")
async def update_organization(
    org_id: str,
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    allowed = ["name", "industry", "revenue_range", "employee_count",
               "address", "gstin", "cin", "dpo_name", "dpo_email"]
    for key, value in payload.items():
        if key in allowed and hasattr(org, key):
            setattr(org, key, value)

    await session.commit()
    await session.refresh(org)
    return {"status": "updated", "organization": org}
