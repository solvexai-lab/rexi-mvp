from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import ContractTemplate

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

@router.get("")
async def list_templates(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ContractTemplate).where(ContractTemplate.org_id == org_id))
    templates = result.scalars().all()
    return [t.model_dump() for t in templates]

@router.post("")
async def create_template(template: ContractTemplate, session: AsyncSession = Depends(get_session)):
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template.model_dump()

@router.get("/{template_id}")
async def get_template(template_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ContractTemplate).where(ContractTemplate.id == template_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    return t.model_dump()

@router.put("/{template_id}")
async def update_template(template_id: str, template: ContractTemplate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ContractTemplate).where(ContractTemplate.id == template_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")
    existing.name = template.name
    existing.category = template.category
    existing.content = template.content
    existing.variables = template.variables
    await session.commit()
    await session.refresh(existing)
    return existing.model_dump()

@router.delete("/{template_id}")
async def delete_template(template_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ContractTemplate).where(ContractTemplate.id == template_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(t)
    await session.commit()
    return {"status": "deleted"}
