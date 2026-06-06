from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import Contract, RiskFinding

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])

@router.get("/dashboard")
async def risk_dashboard(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    from app.models.tables import RiskAssessment
    from sqlalchemy import func

    # Single query: count contracts
    res = await session.execute(select(func.count(Contract.id)).where(Contract.org_id == org_id))
    total_contracts = res.scalar() or 0

    # Cross-database latest assessment per contract (no DISTINCT ON)
    res = await session.execute(
        select(RiskAssessment.contract_id, func.max(RiskAssessment.created_at))
        .where(RiskAssessment.org_id == org_id)
        .group_by(RiskAssessment.contract_id)
    )
    latest_map = {row[0]: row[1] for row in res.all()}

    all_assessments = []
    for cid, latest_dt in latest_map.items():
        res = await session.execute(
            select(RiskAssessment)
            .where(
                RiskAssessment.org_id == org_id,
                RiskAssessment.contract_id == cid,
                RiskAssessment.created_at == latest_dt
            )
            .limit(1)
        )
        a = res.scalar_one_or_none()
        if a:
            all_assessments.append(a)

    # Single query: open findings with severity counts
    res = await session.execute(
        select(RiskFinding.severity, func.count(RiskFinding.id))
        .where(RiskFinding.is_resolved == False)
        .group_by(RiskFinding.severity)
    )
    severity_counts = {row[0]: row[1] for row in res.all()}

    return {
        "total_contracts": total_contracts,
        "avg_risk_score": round(sum(a.overall_score for a in all_assessments) / len(all_assessments), 2) if all_assessments else 0,
        "open_findings": sum(severity_counts.values()),
        "findings_by_severity": {
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
        }
    }

@router.get("/findings")
async def list_findings(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    from app.models.tables import RiskAssessment
    # Filter findings through assessments to enforce org scoping
    # Join to Contract so frontend can link to the source contract
    result = await session.execute(
        select(RiskFinding, RiskAssessment.contract_id, Contract.title.label("contract_title"))
        .join(RiskAssessment, RiskFinding.assessment_id == RiskAssessment.id)
        .join(Contract, RiskAssessment.contract_id == Contract.id)
        .where(RiskAssessment.org_id == org_id)
    )
    rows = result.all()
    return [{"id": f.id, "title": f.title, "severity": f.severity,
             "finding_type": f.finding_type, "is_resolved": f.is_resolved,
             "suggested_amendment": f.suggested_amendment,
             "description": f.description,
             "contract_id": contract_id,
             "contract_title": contract_title} for f, contract_id, contract_title in rows]

@router.put("/findings/{finding_id}/resolve")
async def resolve_finding(finding_id: str, session: AsyncSession = Depends(get_session)):
    from app.models.tables import RiskAssessment
    result = await session.execute(
        select(RiskFinding)
        .join(RiskAssessment, RiskFinding.assessment_id == RiskAssessment.id)
        .where(RiskFinding.id == finding_id)
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.is_resolved = True
    await session.commit()
    return {"id": finding.id, "is_resolved": True}
