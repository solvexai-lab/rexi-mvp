from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Optional
from app.core.database import get_session
from app.models.tables import ContractComment

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])

@router.get("/contracts/{contract_id}")
async def list_comments(contract_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ContractComment).where(ContractComment.contract_id == contract_id).order_by(ContractComment.created_at)
    )
    comments = result.scalars().all()
    return [c.model_dump() for c in comments]

@router.post("/contracts/{contract_id}")
async def create_comment(
    contract_id: str, content: str, clause_id: Optional[str] = None,
    org_id: str = "demo-org", author_name: str = "Legal Team", author_role: str = "reviewer",
    session: AsyncSession = Depends(get_session)
):
    comment = ContractComment(
        contract_id=contract_id, clause_id=clause_id, org_id=org_id,
        author_name=author_name, author_role=author_role, content=content
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment.model_dump()

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ContractComment).where(ContractComment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(comment)
    await session.commit()
    return {"status": "deleted"}
