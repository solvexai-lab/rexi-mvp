"""PageIndex API — hierarchical document tree retrieval."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import ContractTreeIndex
from app.services.pageindex_service import pageindex_service

router = APIRouter(prefix="/api/v1/pageindex", tags=["pageindex"])


class TreeQueryRequest(BaseModel):
    query: str


class TreeQueryResponse(BaseModel):
    results: List[Dict]
    count: int


@router.get("/status")
async def pageindex_status():
    """Return PageIndex service status."""
    return pageindex_service.status()


@router.get("/contracts/{contract_id}/tree")
async def get_contract_tree(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Get the hierarchical tree index for a contract."""
    result = await session.execute(
        select(ContractTreeIndex).where(ContractTreeIndex.contract_id == contract_id)
    )
    tree = result.scalar_one_or_none()
    if not tree:
        raise HTTPException(status_code=404, detail="Tree index not found for this contract")
    return {
        "contract_id": tree.contract_id,
        "doc_name": tree.doc_name,
        "structure": tree.structure,
        "line_count": tree.line_count,
        "node_count": tree.node_count,
    }


@router.post("/contracts/{contract_id}/query", response_model=TreeQueryResponse)
async def query_contract_tree(contract_id: str, req: TreeQueryRequest, session: AsyncSession = Depends(get_session)):
    """Query the contract tree with keywords."""
    result = await session.execute(
        select(ContractTreeIndex).where(ContractTreeIndex.contract_id == contract_id)
    )
    tree = result.scalar_one_or_none()
    if not tree:
        raise HTTPException(status_code=404, detail="Tree index not found for this contract")

    results = pageindex_service.query_tree(
        {"structure": tree.structure},
        req.query,
    )
    return TreeQueryResponse(results=results, count=len(results))


@router.get("/contracts/{contract_id}/flatten")
async def flatten_contract_tree(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Get a flat list of all nodes in the contract tree."""
    result = await session.execute(
        select(ContractTreeIndex).where(ContractTreeIndex.contract_id == contract_id)
    )
    tree = result.scalar_one_or_none()
    if not tree:
        raise HTTPException(status_code=404, detail="Tree index not found for this contract")

    flat = pageindex_service.flatten_tree({"structure": tree.structure})
    return {"contract_id": contract_id, "nodes": flat, "count": len(flat)}
