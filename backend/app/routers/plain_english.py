"""Plain English Summary router — adapted from ClauseIQ patterns."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from app.core.database import get_session
from app.models.tables import Contract, ContractClause, PlainEnglishSummary
from app.services.gemini_service import translate_clause_to_plain_english, analyze_clause_risk, GeminiUnavailableError
from app.services.langfuse_service import langfuse_observer

router = APIRouter(prefix="/api/v1/plain-english", tags=["plain-english"])


@router.post("/contracts/{contract_id}/generate")
@langfuse_observer(name="plain_english.generate")
async def generate_plain_english(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Generate plain English summaries for all clauses in a contract."""
    # Verify contract exists
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Get clauses
    res_clauses = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
    clauses = res_clauses.scalars().all()

    if not clauses:
        raise HTTPException(status_code=400, detail="No clauses extracted for this contract")

    summaries = []
    for cl in clauses:
        # Check if already cached
        existing = await session.execute(
            select(PlainEnglishSummary).where(
                PlainEnglishSummary.contract_id == contract_id,
                PlainEnglishSummary.clause_id == cl.id
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Generate using Gemini
        try:
            analysis = await translate_clause_to_plain_english(cl.clause_type, cl.clause_text)
        except GeminiUnavailableError as e:
            raise HTTPException(status_code=503, detail=str(e))

        summary = PlainEnglishSummary(
            contract_id=contract_id,
            clause_id=cl.id,
            clause_type=cl.clause_type,
            original_text=cl.clause_text,
            plain_english=analysis.get("plain_english", ""),
            risk_level=analysis.get("risk_level", "low").lower(),
            risk_explanation=analysis.get("risk_explanation", ""),
            suggestions=analysis.get("suggestions", "")
        )
        session.add(summary)
        summaries.append(summary)

    await session.commit()

    return {
        "contract_id": contract_id,
        "generated": len(summaries),
        "summaries": [
            {
                "id": s.id,
                "clause_type": s.clause_type,
                "plain_english": s.plain_english,
                "risk_level": s.risk_level,
                "risk_explanation": s.risk_explanation,
                "suggestions": s.suggestions,
            }
            for s in summaries
        ]
    }


@router.get("/contracts/{contract_id}")
async def get_plain_english(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Get cached plain English summaries for a contract."""
    result = await session.execute(
        select(PlainEnglishSummary).where(PlainEnglishSummary.contract_id == contract_id)
    )
    summaries = result.scalars().all()

    if not summaries:
        # Auto-generate if none exist
        return await generate_plain_english(contract_id, session)

    return {
        "contract_id": contract_id,
        "generated": len(summaries),
        "summaries": [
            {
                "id": s.id,
                "clause_id": s.clause_id,
                "clause_type": s.clause_type,
                "original_text": s.original_text,
                "plain_english": s.plain_english,
                "risk_level": s.risk_level,
                "risk_explanation": s.risk_explanation,
                "suggestions": s.suggestions,
            }
            for s in summaries
        ]
    }


@router.post("/clauses/{clause_id}/explain-risk")
@langfuse_observer(name="plain_english.explain_risk")
async def explain_clause_risk(clause_id: str, session: AsyncSession = Depends(get_session)):
    """Get detailed explainable risk analysis for a single clause.
    Adapted from ContractGuard's analyzer.py.
    """
    result = await session.execute(select(ContractClause).where(ContractClause.id == clause_id))
    clause = result.scalar_one_or_none()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    analysis = await analyze_clause_risk(clause.clause_text)

    return {
        "clause_id": clause_id,
        "clause_type": clause.clause_type,
        "contract_type": analysis.get("contract_type", "unknown"),
        "summary": analysis.get("summary", ""),
        "red_flags": analysis.get("red_flags", []),
        "warnings": analysis.get("warnings", []),
        "good_clauses": analysis.get("good_clauses", []),
        "missing_protections": analysis.get("missing_protections", []),
        "fairness_score": analysis.get("fairness_score", 50),
        "fairness_grade": analysis.get("fairness_grade", "C"),
    }
