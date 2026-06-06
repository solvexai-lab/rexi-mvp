"""Redline diff router — adapted from legal-redline-tools + multi-agent-contract-platform."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Dict
from app.core.database import get_session
from app.models.tables import Contract, ContractClause, ContractVersion
from app.services.semantic_diff import compare_contracts, compare_clauses
from app.services.gemini_service import what_if_simulate, GeminiUnavailableError

router = APIRouter(prefix="/api/v1/redline", tags=["redline"])


@router.get("/contracts/{contract_id}/versions")
async def list_contract_versions(
    contract_id: str,
    session: AsyncSession = Depends(get_session)
):
    """List all stored versions for a contract."""
    result = await session.execute(
        select(ContractVersion).where(ContractVersion.contract_id == contract_id).order_by(ContractVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return {
        "contract_id": contract_id,
        "versions": [
            {
                "id": v.id,
                "version_number": v.version_number,
                "title": v.title,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "created_by": v.created_by,
            }
            for v in versions
        ]
    }


@router.get("/contracts/{contract_id}/compare/{other_contract_id}")
async def compare_two_contracts(
    contract_id: str,
    other_contract_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Semantic clause-level comparison between two contracts.
    Adapted from multi-agent-contract clause_compare.py.
    """
    # Verify both contracts exist
    for cid in [contract_id, other_contract_id]:
        result = await session.execute(select(Contract).where(Contract.id == cid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Contract {cid} not found")

    # Get clauses
    res_a = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
    clauses_a = [{"clause_type": c.clause_type, "clause_text": c.clause_text} for c in res_a.scalars().all()]

    res_b = await session.execute(select(ContractClause).where(ContractClause.contract_id == other_contract_id))
    clauses_b = [{"clause_type": c.clause_type, "clause_text": c.clause_text} for c in res_b.scalars().all()]

    results = await compare_contracts(clauses_a, clauses_b)

    return {
        "contract_a": contract_id,
        "contract_b": other_contract_id,
        "comparison": [
            {
                "clause_type": r.old_text[:30] if not r.new_text else r.new_text[:30],  # fallback
                "label": r.label,
                "change_summary": r.change_summary,
                "key_differences": r.key_differences,
                "similarity_score": r.similarity_score,
                "risk_delta": r.risk_delta,
                "old_text": r.old_text[:500] if r.old_text else None,
                "new_text": r.new_text[:500] if r.new_text else None,
            }
            for r in results
        ]
    }


@router.post("/clauses/compare")
async def compare_two_clauses(data: dict):
    """Compare two clause texts directly."""
    old_text = data.get("old_text", "")
    new_text = data.get("new_text", "")

    result = await compare_clauses(old_text, new_text)

    return {
        "label": result.label,
        "change_summary": result.change_summary,
        "key_differences": result.key_differences,
        "similarity_score": result.similarity_score,
        "risk_delta": result.risk_delta,
        "old_text": result.old_text[:500] if result.old_text else None,
        "new_text": result.new_text[:500] if result.new_text else None,
    }


@router.post("/what-if")
async def what_if_scenario(data: dict):
    """What-if scenario simulation.
    Compare original vs proposed clause against playbook standard.
    """
    original = data.get("original_clause", "")
    proposed = data.get("proposed_clause", "")
    playbook = data.get("playbook_standard", "Standard industry terms apply.")

    try:
        result = await what_if_simulate(original, proposed, playbook)
    except GeminiUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return result
