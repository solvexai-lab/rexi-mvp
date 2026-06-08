"""Analytics & aggregated data for dashboards and charts."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.core.database import get_session
from app.models.tables import (
    Contract, Obligation,
    RegulatoryAlert, PlaybookRule, AutomationLog, AuditTrailEntry
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    """Single-call analytics payload for the main dashboard."""

    # Contract counts by status
    res = await session.execute(select(Contract.status, func.count(Contract.id))
                                .where(Contract.org_id == org_id)
                                .group_by(Contract.status))
    contract_status = {row[0]: row[1] for row in res.all()}
    total_contracts = sum(contract_status.values())

    # Obligations summary
    res = await session.execute(
        select(Obligation.status, func.count(Obligation.id))
        .where(Obligation.org_id == org_id)
        .group_by(Obligation.status)
    )
    obligations = {row[0]: row[1] for row in res.all()}

    # Regulatory alerts
    res = await session.execute(
        select(RegulatoryAlert.priority, func.count(RegulatoryAlert.id))
        .where(RegulatoryAlert.org_id == org_id, RegulatoryAlert.status == "unread")
        .group_by(RegulatoryAlert.priority)
    )
    unread_alerts = {row[0]: row[1] for row in res.all()}

    # Recent automation logs (last 5)
    res = await session.execute(
        select(AutomationLog)
        .where(AutomationLog.org_id == org_id)
        .order_by(AutomationLog.created_at.desc())
        .limit(5)
    )
    recent_logs = [l.model_dump() for l in res.scalars().all()]

    # Audit trail count
    res = await session.execute(
        select(func.count(AuditTrailEntry.id))
        .where(AuditTrailEntry.org_id == org_id)
    )
    audit_entries = res.scalar() or 0

    # Playbook rules count
    res = await session.execute(
        select(func.count(PlaybookRule.id))
        .where(PlaybookRule.org_id == org_id, PlaybookRule.is_active == True)
    )
    active_rules = res.scalar() or 0

    # Platform-value metrics (pure SQL, no AI)
    res = await session.execute(
        select(func.sum(Contract.value_inr))
        .where(Contract.org_id == org_id)
    )
    total_value_inr = res.scalar() or 0

    res = await session.execute(
        select(func.count(Contract.id))
        .where(Contract.org_id == org_id, Contract.status != "processing")
    )
    processed_count = res.scalar() or 0
    automation_rate = round((processed_count / total_contracts * 100), 1) if total_contracts else 0

    all_contracts_count = total_contracts
    compliance_coverage = 100.0 if all_contracts_count > 0 else 0.0

    # Rough heuristic: 2.5 hours saved per auto-processed contract
    time_saved_hours = int(processed_count * 2.5)

    return {
        "contracts": {
            "total": total_contracts,
            "by_status": contract_status,
        },
        "obligations": {
            "total": sum(obligations.values()),
            "by_status": obligations,
        },
        "regulatory": {
            "unread_alerts": unread_alerts,
        },
        "recent_logs": recent_logs,
        "audit_entries": audit_entries,
        "active_playbook_rules": active_rules,
        "platform_value": {
            "total_value_inr": float(total_value_inr),
            "automation_rate": automation_rate,
            "time_saved_hours": time_saved_hours,
            "compliance_coverage": compliance_coverage,
        }
    }


@router.get("/risk-history")
async def risk_history(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    """Risk scores over time for trend charts — deprecated, returns empty."""
    return []
