from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import PlaybookRule, Contract, ContractClause
from app.services.playbook_evaluator import evaluate_contract

router = APIRouter(prefix="/api/v1/playbook", tags=["playbook"])

@router.get("/rules")
async def list_rules(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlaybookRule).where(PlaybookRule.org_id == org_id))
    rules = result.scalars().all()
    return [r.model_dump() for r in rules]

@router.post("/rules")
async def create_rule(rule: PlaybookRule, session: AsyncSession = Depends(get_session)):
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule.model_dump()

@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, rule: PlaybookRule, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlaybookRule).where(PlaybookRule.id == rule_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Not found")
    existing.rule_name = rule.rule_name
    existing.rule_type = rule.rule_type
    existing.condition = rule.condition
    existing.threshold_value = rule.threshold_value
    existing.severity = rule.severity
    existing.is_active = rule.is_active
    await session.commit()
    await session.refresh(existing)
    return existing.model_dump()

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlaybookRule).where(PlaybookRule.id == rule_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(r)
    await session.commit()
    return {"status": "deleted"}


@router.get("/summary")
async def playbook_summary(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    """Aggregate playbook evaluation across all contracts in the org."""
    res_rules = await session.execute(
        select(PlaybookRule).where(PlaybookRule.org_id == org_id, PlaybookRule.is_active == True)
    )
    rules = res_rules.scalars().all()

    res_contracts = await session.execute(
        select(Contract).where(Contract.org_id == org_id)
    )
    contracts = res_contracts.scalars().all()

    total_violations = 0
    contracts_with_violations = 0
    severity_breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    contract_scores = []

    for contract in contracts:
        res_clauses = await session.execute(
            select(ContractClause).where(ContractClause.contract_id == contract.id)
        )
        clauses = [cl.model_dump() for cl in res_clauses.scalars().all()]

        evaluation = evaluate_contract(
            contract_type=contract.contract_type or "vendor",
            clauses=clauses,
            rules=rules,
        )

        v_count = len(evaluation["violations"])
        if v_count > 0:
            contracts_with_violations += 1
        total_violations += v_count
        contract_scores.append(evaluation["score"])

        for sev, count in evaluation["severity_breakdown"].items():
            severity_breakdown[sev] = severity_breakdown.get(sev, 0) + count

    avg_score = round(sum(contract_scores) / len(contract_scores), 1) if contract_scores else 0

    return {
        "total_violations": total_violations,
        "contracts_with_violations": contracts_with_violations,
        "total_contracts_evaluated": len(contracts),
        "average_score": avg_score,
        "severity_breakdown": severity_breakdown,
    }
