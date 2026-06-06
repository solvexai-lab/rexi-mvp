"""Counterparty risk dashboard router.
Aggregates contract data per vendor/counterparty using SQL.
Zero AI calls — pure deterministic aggregation.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_session

router = APIRouter(prefix="/api/v1/counterparties", tags=["counterparties"])


@router.get("/dashboard")
async def counterparty_dashboard(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    """Aggregate risk and contract metrics per counterparty.
    Pure SQL — no AI calls.
    Uses subquery to avoid double-counting from risk_findings JOIN.
    """
    query = text("""
        WITH contract_risk AS (
            SELECT
                c.id as contract_id,
                c.counterparty_name,
                c.value_inr,
                c.status,
                c.end_date,
                r.overall_score
            FROM contracts c
            LEFT JOIN risk_assessments r ON c.id = r.contract_id
            WHERE c.org_id = :org_id
        ),
        finding_counts AS (
            SELECT
                c.counterparty_name,
                COUNT(DISTINCT CASE WHEN rf.severity = 'critical' THEN rf.id END) as critical_findings,
                COUNT(DISTINCT CASE WHEN rf.severity = 'high' THEN rf.id END) as high_findings
            FROM contracts c
            LEFT JOIN risk_assessments r ON c.id = r.contract_id
            LEFT JOIN risk_findings rf ON r.id = rf.assessment_id AND rf.is_resolved = false
            WHERE c.org_id = :org_id
            GROUP BY c.counterparty_name
        )
        SELECT
            cr.counterparty_name,
            COUNT(DISTINCT cr.contract_id) as contract_count,
            SUM(DISTINCT cr.value_inr) as total_value,
            AVG(cr.overall_score) as avg_risk_score,
            COALESCE(fc.critical_findings, 0) as critical_findings,
            COALESCE(fc.high_findings, 0) as high_findings,
            MIN(cr.end_date) as next_renewal,
            COUNT(DISTINCT CASE WHEN cr.status = 'active' THEN cr.contract_id END) as active_count
        FROM contract_risk cr
        LEFT JOIN finding_counts fc ON cr.counterparty_name = fc.counterparty_name
        WHERE cr.counterparty_name != ''
        GROUP BY cr.counterparty_name, fc.critical_findings, fc.high_findings
        ORDER BY avg_risk_score DESC NULLS LAST
    """)

    result = await session.execute(query, {"org_id": org_id})
    rows = result.mappings().all()

    return {
        "org_id": org_id,
        "counterparties": [
            {
                "name": row["counterparty_name"],
                "contract_count": row["contract_count"],
                "total_value_inr": float(row["total_value"] or 0),
                "avg_risk_score": round(float(row["avg_risk_score"] or 0), 2),
                "critical_findings": row["critical_findings"],
                "high_findings": row["high_findings"],
                "next_renewal": row["next_renewal"],
                "active_count": row["active_count"],
                "risk_tier": "high" if (row["avg_risk_score"] or 0) >= 0.7 else "medium" if (row["avg_risk_score"] or 0) >= 0.4 else "low",
            }
            for row in rows
        ]
    }


@router.get("/{counterparty_name}/contracts")
async def counterparty_contracts(counterparty_name: str, org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    """List all contracts for a specific counterparty."""
    from sqlmodel import select
    from app.models.tables import Contract

    result = await session.execute(
        select(Contract).where(
            Contract.org_id == org_id,
            Contract.counterparty_name == counterparty_name
        )
    )
    contracts = result.scalars().all()
    return {
        "counterparty_name": counterparty_name,
        "contracts": [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "value_inr": c.value_inr,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "contract_type": c.contract_type,
            }
            for c in contracts
        ]
    }
