"""Analytics & aggregated data for dashboards and charts."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.core.database import get_session
from app.models.tables import (
    Contract, RiskAssessment, RiskFinding, Obligation,
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

    # Latest risk assessment per contract
    res = await session.execute(
        select(RiskAssessment.contract_id,
               func.max(RiskAssessment.created_at).label("latest"))
        .where(RiskAssessment.org_id == org_id)
        .group_by(RiskAssessment.contract_id)
    )
    latest_assessment_map = {row[0]: row[1] for row in res.all()}

    avg_risk = 0.0
    if latest_assessment_map:
        # Average only the LATEST assessment per contract
        latest_ids = []
        for cid, latest_dt in latest_assessment_map.items():
            res = await session.execute(
                select(RiskAssessment.id)
                .where(
                    RiskAssessment.org_id == org_id,
                    RiskAssessment.contract_id == cid,
                    RiskAssessment.created_at == latest_dt
                )
                .limit(1)
            )
            row = res.scalar_one_or_none()
            if row:
                latest_ids.append(row)
        if latest_ids:
            res = await session.execute(
                select(func.avg(RiskAssessment.overall_score))
                .where(RiskAssessment.id.in_(latest_ids))
            )
            avg_risk = round(res.scalar() or 0.0, 2)

    # Open findings (scoped to org via RiskAssessment join)
    res = await session.execute(
        select(func.count(RiskFinding.id))
        .join(RiskAssessment, RiskFinding.assessment_id == RiskAssessment.id)
        .where(RiskFinding.is_resolved == False, RiskAssessment.org_id == org_id)
    )
    open_findings = res.scalar() or 0

    # Findings by severity
    res = await session.execute(
        select(RiskFinding.severity, func.count(RiskFinding.id))
        .join(RiskAssessment, RiskFinding.assessment_id == RiskAssessment.id)
        .where(RiskFinding.is_resolved == False, RiskAssessment.org_id == org_id)
        .group_by(RiskFinding.severity)
    )
    findings_by_severity = {row[0]: row[1] for row in res.all()}

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

    res = await session.execute(
        select(func.count(Contract.id))
        .where(Contract.org_id == org_id)
    )
    all_contracts_count = res.scalar() or 0
    res = await session.execute(
        select(func.count(RiskAssessment.contract_id.distinct()))
        .where(RiskAssessment.org_id == org_id)
    )
    assessed_count = res.scalar() or 0
    compliance_coverage = round((assessed_count / all_contracts_count * 100), 1) if all_contracts_count else 0

    # Rough heuristic: 2.5 hours saved per auto-processed contract
    time_saved_hours = int(processed_count * 2.5)

    return {
        "contracts": {
            "total": total_contracts,
            "by_status": contract_status,
        },
        "risk": {
            "avg_score": avg_risk,
            "open_findings": open_findings,
            "by_severity": findings_by_severity,
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
    """Risk scores over time for trend charts."""
    res = await session.execute(
        select(RiskAssessment)
        .where(RiskAssessment.org_id == org_id)
        .order_by(RiskAssessment.created_at)
    )
    assessments = res.scalars().all()
    return [
        {
            "date": a.created_at.strftime("%Y-%m-%d"),
            "overall": a.overall_score,
            "playbook": a.playbook_score,
            "law": a.law_score,
            "regulatory": a.regulatory_score,
        }
        for a in assessments
    ]
