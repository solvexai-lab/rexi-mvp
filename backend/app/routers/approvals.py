from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone
from app.core.database import get_session
from app.models.tables import Contract, ApprovalStage, Notification

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])

VALID_TRANSITIONS = {
    "draft": ["in_review"],
    "in_review": ["approved", "rejected"],
    "approved": ["signed", "active"],
    "signed": ["active"],
    "active": ["expired", "terminated"],
    "rejected": ["draft"],
    "expired": ["draft"],
    "terminated": ["draft"],
}

APPROVAL_STAGES = ["legal_review", "finance_review", "ceo_review"]

@router.get("/contracts/{contract_id}/stages")
async def get_approval_stages(contract_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ApprovalStage).where(ApprovalStage.contract_id == contract_id).order_by(ApprovalStage.created_at)
    )
    stages = result.scalars().all()
    return [s.model_dump() for s in stages]

@router.post("/contracts/{contract_id}/submit")
async def submit_for_approval(contract_id: str, org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status not in ["draft", "rejected"]:
        raise HTTPException(status_code=400, detail=f"Cannot submit from status {contract.status}")
    contract.status = "in_review"

    for stage_name in APPROVAL_STAGES:
        stage = ApprovalStage(
            contract_id=contract_id, org_id=org_id, stage_name=stage_name,
            approver_name=f"{stage_name.replace('_', ' ').title()} Approver",
            approver_email=f"{stage_name}@acme.com", status="pending"
        )
        session.add(stage)

    notify = Notification(
        org_id=org_id, title="Contract submitted for approval",
        message=f"{contract.title} is awaiting approval", notification_type="approval",
        link=f"/contracts/{contract_id}"
    )
    session.add(notify)
    await session.commit()
    return {"status": "submitted", "stages": APPROVAL_STAGES}

@router.put("/stages/{stage_id}/approve")
async def approve_stage(stage_id: str, comment: str = "", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ApprovalStage).where(ApprovalStage.id == stage_id))
    stage = result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    if stage.status != "pending":
        raise HTTPException(status_code=400, detail="Stage already resolved")
    stage.status = "approved"
    stage.comment = comment
    stage.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Check if all stages approved
    res = await session.execute(
        select(ApprovalStage).where(ApprovalStage.contract_id == stage.contract_id)
    )
    stages = res.scalars().all()
    if all(s.status == "approved" for s in stages):
        cres = await session.execute(select(Contract).where(Contract.id == stage.contract_id))
        contract = cres.scalar_one_or_none()
        if contract:
            contract.status = "approved"
            notify = Notification(
                org_id=stage.org_id, title="Contract fully approved",
                message=f"{contract.title} has been approved by all stages", notification_type="success",
                link=f"/contracts/{stage.contract_id}"
            )
            session.add(notify)
    await session.commit()
    return {"status": "approved"}

@router.put("/stages/{stage_id}/reject")
async def reject_stage(stage_id: str, comment: str = "", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(ApprovalStage).where(ApprovalStage.id == stage_id))
    stage = result.scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    if stage.status != "pending":
        raise HTTPException(status_code=400, detail="Stage already resolved")
    stage.status = "rejected"
    stage.comment = comment
    stage.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    cres = await session.execute(select(Contract).where(Contract.id == stage.contract_id))
    contract = cres.scalar_one_or_none()
    if contract:
        contract.status = "rejected"
        notify = Notification(
            org_id=stage.org_id, title="Contract rejected",
            message=f"{contract.title} was rejected at {stage.stage_name}", notification_type="warning",
            link=f"/contracts/{stage.contract_id}"
        )
        session.add(notify)
    await session.commit()
    return {"status": "rejected"}

@router.post("/contracts/{contract_id}/transition")
async def transition_status(contract_id: str, new_status: str, org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    current = contract.status
    allowed = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current} to {new_status}. Allowed: {allowed}")
    contract.status = new_status
    notify = Notification(
        org_id=org_id, title="Contract status changed",
        message=f"{contract.title} moved from {current} to {new_status}", notification_type="info",
        link=f"/contracts/{contract_id}"
    )
    session.add(notify)
    await session.commit()
    return {"status": new_status, "previous": current}
