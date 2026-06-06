"""Contract fingerprint router — MinHash + Jaccard similarity.

Deterministic similarity detection across the contract portfolio.
No AI required. Finds duplicates, near-duplicates, and contract families.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from app.core.database import get_session
from app.models.tables import Contract, ContractClause
from app.services.contract_fingerprint import (
    fingerprint_service,
    jaccard_similarity,
)

router = APIRouter(prefix="/api/v1/fingerprint", tags=["fingerprint"])


async def _load_contracts_with_clauses(
    session: AsyncSession,
    org_id: Optional[str] = None,
    contract_ids: Optional[List[str]] = None,
) -> List[dict]:
    """Load contracts and their clauses for fingerprinting."""
    stmt = select(Contract)
    if org_id:
        stmt = stmt.where(Contract.org_id == org_id)
    if contract_ids:
        stmt = stmt.where(Contract.id.in_(contract_ids))
    result = await session.execute(stmt)
    contracts = result.scalars().all()

    records = []
    for c in contracts:
        clause_res = await session.execute(
            select(ContractClause).where(ContractClause.contract_id == c.id)
        )
        clauses = clause_res.scalars().all()
        records.append(
            {
                "id": c.id,
                "title": c.title,
                "contract_type": c.contract_type,
                "counterparty_name": c.counterparty_name,
                "parsed_text": c.parsed_text or "",
                "clauses": [
                    {"clause_type": cl.clause_type, "clause_text": cl.clause_text}
                    for cl in clauses
                ],
            }
        )
    return records


@router.post("/analyze")
async def analyze_portfolio(
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    """Generate fingerprints and find similar contracts across the portfolio.

    Body: {"org_id": "...", "threshold": 0.65, "contract_ids": ["..."]}
    If contract_ids omitted, analyzes all contracts for the org.
    """
    org_id = payload.get("org_id")
    threshold = payload.get("threshold", 0.65)
    contract_ids = payload.get("contract_ids")

    records = await _load_contracts_with_clauses(session, org_id, contract_ids)
    if len(records) < 2:
        return {
            "contracts_analyzed": len(records),
            "similar_pairs": [],
            "clusters": [],
            "message": "Need at least 2 contracts to compare." if len(records) < 2 else "No similar contracts found.",
        }

    fingerprints = await fingerprint_service.fingerprint_contracts(records)
    similar_pairs = fingerprint_service.find_similar_pairs(fingerprints, threshold=threshold)
    clusters = fingerprint_service.cluster_contracts(fingerprints, threshold=max(threshold - 0.05, 0.5))

    return {
        "contracts_analyzed": len(records),
        "threshold": threshold,
        "similar_pairs": [
            {
                "contract_a_id": p.contract_a_id,
                "contract_a_title": p.contract_a_title,
                "contract_b_id": p.contract_b_id,
                "contract_b_title": p.contract_b_title,
                "similarity": p.similarity,
            }
            for p in similar_pairs
        ],
        "clusters": [
            {
                "cluster_id": c.cluster_id,
                "representative_title": c.representative_title,
                "contract_ids": c.contract_ids,
                "size": len(c.contract_ids),
                "avg_similarity": c.avg_similarity,
            }
            for c in clusters
        ],
    }


@router.get("/contracts/{contract_id}/compare")
async def compare_single_contract(
    contract_id: str,
    org_id: Optional[str] = Query(None),
    threshold: float = Query(0.65),
    session: AsyncSession = Depends(get_session),
):
    """Find contracts similar to a given contract."""
    # Load target contract
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Load all contracts in org
    records = await _load_contracts_with_clauses(session, org_id=target.org_id)
    if len(records) < 2:
        return {"target_contract_id": contract_id, "matches": [], "message": "No other contracts to compare."}

    fingerprints = await fingerprint_service.fingerprint_contracts(records)
    target_fp = next((fp for fp in fingerprints if fp.contract_id == contract_id), None)
    if not target_fp:
        return {"target_contract_id": contract_id, "matches": [], "message": "Could not fingerprint target contract."}

    matches = []
    for fp in fingerprints:
        if fp.contract_id == contract_id:
            continue
        sim = jaccard_similarity(target_fp.signature, fp.signature)
        if sim >= threshold:
            matches.append(
                {
                    "contract_id": fp.contract_id,
                    "title": fp.title,
                    "contract_type": fp.contract_type,
                    "similarity": round(sim, 3),
                }
            )

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return {
        "target_contract_id": contract_id,
        "target_title": target.title,
        "matches": matches,
    }


@router.post("/contracts/{contract_id}/generate")
async def generate_fingerprint(
    contract_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Generate and return the MinHash fingerprint for a single contract."""
    records = await _load_contracts_with_clauses(session, contract_ids=[contract_id])
    if not records:
        raise HTTPException(status_code=404, detail="Contract not found")

    fingerprints = await fingerprint_service.fingerprint_contracts(records)
    fp = fingerprints[0]

    return {
        "contract_id": fp.contract_id,
        "title": fp.title,
        "shingle_count": len(fp.shingles),
        "signature_length": len(fp.signature),
        "signature_preview": fp.signature[:8],
    }
