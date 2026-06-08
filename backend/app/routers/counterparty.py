"""Counterparty dashboard router.
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
    """Aggregate contract metrics per counterparty.
    Pure SQL — no AI calls.
    """
    query = text("""
        SELECT
            c.counterparty_name,
            COUNT(DISTINCT c.id) as contract_count,
            SUM(c.value_inr) as total_value,
            MIN(c.end_date) as next_renewal,
            COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_count
        FROM contracts c
        WHERE c.org_id = :org_id
          AND c.counterparty_name != ''
        GROUP BY c.counterparty_name
        ORDER BY total_value DESC NULLS LAST
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
                "avg_risk_score": 0,
                "critical_findings": 0,
                "high_findings": 0,
                "next_renewal": row["next_renewal"],
                "active_count": row["active_count"],
                "risk_tier": "low",
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
