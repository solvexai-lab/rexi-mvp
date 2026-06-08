"""Knowledge Graph router — 3-Pillar Impact Engine.

All impact endpoints have TWO modes:
  1. SQL-first (deterministic, always works) — returns structured data from PostgreSQL
  2. Neo4j graph (optional, requires running Neo4j) — returns graph paths

The demo narrative: "The graph is a VIEW. The truth lives in SQL."
"""
import re
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.services.knowledge_graph_service import kg_service
from app.models.tables import (
    Contract, ContractClause, PlaybookRule,
    RegulatoryUpdate, RegulatoryAlert,
    EnforceabilityBenchmark,
)

router = APIRouter(prefix="/api/v1/graph", tags=["knowledge-graph"])


def _check_neo4j():
    if not kg_service._available:
        raise HTTPException(status_code=503, detail="Neo4j Knowledge Graph is not available")


# ──────────────────────────── Neo4j endpoints (optional) ────────────────────────────

@router.get("/contracts/{contract_id}/network")
def contract_network(contract_id: str):
    _check_neo4j()
    return kg_service.get_contract_network(contract_id)


@router.get("/regulation-impact/{regulation_id}")
def regulation_impact_neo4j(regulation_id: str):
    _check_neo4j()
    return kg_service.get_regulation_impact(regulation_id)


@router.get("/org/{org_id}/contracts")
def org_contracts_neo4j(org_id: str):
    _check_neo4j()
    return kg_service.get_org_contracts_summary(org_id)


# ──────────────────────────── SQL-first 3-Pillar Impact ────────────────────────────

@router.get("/impact/regulation/{update_id}")
async def regulation_impact_sql(
    update_id: str,
    org_id: str = "demo-org",
    session: AsyncSession = Depends(get_session),
):
    """Find all contracts affected by a regulatory update — using SQL only.

    Logic: RegulatoryUpdate.affected_clause_types → ContractClause.clause_type → Contract
    """
    # Load the regulatory update
    result = await session.execute(select(RegulatoryUpdate).where(RegulatoryUpdate.id == update_id))
    update = result.scalar_one_or_none()
    if not update:
        raise HTTPException(status_code=404, detail="Regulatory update not found")

    affected_types = update.affected_clause_types or []
    if not affected_types:
        return {
            "update_id": update_id,
            "title": update.title,
            "affected_clause_types": [],
            "contracts": [],
            "source": "sql",
        }

    # Find all clauses matching affected types
    result = await session.execute(
        select(ContractClause, Contract)
        .join(Contract, ContractClause.contract_id == Contract.id)
        .where(
            ContractClause.clause_type.in_(affected_types),
            Contract.org_id == org_id,
        )
    )
    rows = result.all()

    contracts_map: Dict[str, Dict[str, Any]] = {}
    for clause, contract in rows:
        if contract.id not in contracts_map:
            contracts_map[contract.id] = {
                "contract_id": contract.id,
                "title": contract.title,
                "contract_type": contract.contract_type,
                "counterparty_name": contract.counterparty_name,
                "clauses": [],
            }
        contracts_map[contract.id]["clauses"].append({
            "clause_type": clause.clause_type,
            "clause_text": clause.clause_text[:300],
            "page_number": clause.page_number,
        })

    return {
        "update_id": update_id,
        "title": update.title,
        "effective_date": update.effective_date,
        "affected_clause_types": affected_types,
        "contracts_affected": len(contracts_map),
        "contracts": list(contracts_map.values()),
        "source": "sql",
    }


@router.get("/impact/playbook/{rule_id}")
async def playbook_impact_sql(
    rule_id: str,
    org_id: str = "demo-org",
    session: AsyncSession = Depends(get_session),
):
    """Find all contracts that violate a specific playbook rule — using SQL only.

    Logic: PlaybookRule → match clause_type → apply condition → return violations.
    """
    result = await session.execute(
        select(PlaybookRule).where(PlaybookRule.id == rule_id, PlaybookRule.org_id == org_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Playbook rule not found")

    # Load all contracts + clauses for this org
    result = await session.execute(
        select(Contract, ContractClause)
        .join(ContractClause, ContractClause.contract_id == Contract.id)
        .where(Contract.org_id == org_id)
    )
    rows = result.all()

    # Group clauses by contract
    contract_clauses: Dict[str, Dict[str, Any]] = {}
    for contract, clause in rows:
        if contract.id not in contract_clauses:
            contract_clauses[contract.id] = {"contract": contract, "clauses": []}
        contract_clauses[contract.id]["clauses"].append(clause)

    violations = []
    for cid, data in contract_clauses.items():
        contract = data["contract"]
        clauses = data["clauses"]
        matching = [c for c in clauses if c.clause_type == rule.rule_type]

        if rule.condition == "must_have":
            if not matching:
                violations.append({
                    "contract_id": contract.id,
                    "title": contract.title,
                    "clause_type": rule.rule_type,
                    "clause_text": None,
                    "severity": rule.severity,
                    "reason": f"Missing required clause: {rule.rule_type}",
                })
        elif rule.condition == "max_value":
            threshold = _extract_number(rule.threshold_value)
            for cl in matching:
                val = _extract_number(cl.clause_text)
                if val is not None and threshold is not None and val > threshold:
                    violations.append({
                        "contract_id": contract.id,
                        "title": contract.title,
                        "clause_type": cl.clause_type,
                        "clause_text": cl.clause_text[:300],
                        "severity": rule.severity,
                        "reason": f"Value {val} exceeds max threshold {threshold}",
                    })
        elif rule.condition == "min_value":
            threshold = _extract_number(rule.threshold_value)
            for cl in matching:
                val = _extract_number(cl.clause_text)
                if val is not None and threshold is not None and val < threshold:
                    violations.append({
                        "contract_id": contract.id,
                        "title": contract.title,
                        "clause_type": cl.clause_type,
                        "clause_text": cl.clause_text[:300],
                        "severity": rule.severity,
                        "reason": f"Value {val} below min threshold {threshold}",
                    })

    return {
        "rule_id": rule_id,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "condition": rule.condition,
        "threshold_value": rule.threshold_value,
        "severity": rule.severity,
        "contracts_scanned": len(contract_clauses),
        "violations_found": len(violations),
        "violations": violations,
        "source": "sql",
    }


@router.get("/impact/statute/{benchmark_id}")
async def statute_impact_sql(
    benchmark_id: str,
    org_id: str = "demo-org",
    session: AsyncSession = Depends(get_session),
):
    """Find all clauses governed by a statute/enforceability benchmark — using SQL only.

    Logic: EnforceabilityBenchmark.clause_type → ContractClause → Contract
    """
    result = await session.execute(
        select(EnforceabilityBenchmark).where(EnforceabilityBenchmark.id == benchmark_id)
    )
    benchmark = result.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Statute benchmark not found")

    result = await session.execute(
        select(ContractClause, Contract)
        .join(Contract, ContractClause.contract_id == Contract.id)
        .where(
            ContractClause.clause_type == benchmark.clause_type,
            Contract.org_id == org_id,
        )
    )
    rows = result.all()

    contracts_map: Dict[str, Dict[str, Any]] = {}
    for clause, contract in rows:
        if contract.id not in contracts_map:
            contracts_map[contract.id] = {
                "contract_id": contract.id,
                "title": contract.title,
                "contract_type": contract.contract_type,
                "clauses": [],
            }
        contracts_map[contract.id]["clauses"].append({
            "clause_type": clause.clause_type,
            "clause_text": clause.clause_text[:300],
            "page_number": clause.page_number,
            "enforceability_score": benchmark.enforceability_score,
            "statute_act": benchmark.statute_act,
            "section_number": benchmark.section_number,
        })

    return {
        "benchmark_id": benchmark_id,
        "statute_act": benchmark.statute_act,
        "section_number": benchmark.section_number,
        "clause_type": benchmark.clause_type,
        "enforceability_score": benchmark.enforceability_score,
        "conditions": benchmark.conditions,
        "contracts_governed": len(contracts_map),
        "contracts": list(contracts_map.values()),
        "source": "sql",
    }


@router.post("/rescan-playbook")
async def rescan_playbook(
    org_id: str = "demo-org",
    session: AsyncSession = Depends(get_session),
):
    """Re-analyze ALL contracts against current playbook rules — deterministic SQL only.

    Returns new violations found. No Neo4j required. No AI required.
    """
    # Load active rules
    result = await session.execute(
        select(PlaybookRule).where(
            PlaybookRule.org_id == org_id,
            PlaybookRule.is_active == True,
        )
    )
    rules = result.scalars().all()
    if not rules:
        return {"org_id": org_id, "rules_scanned": 0, "violations_found": 0, "violations": [], "source": "sql"}

    # Load all contracts + clauses
    result = await session.execute(
        select(Contract, ContractClause)
        .join(ContractClause, ContractClause.contract_id == Contract.id)
        .where(Contract.org_id == org_id)
    )
    rows = result.all()

    # Group by contract
    contract_map: Dict[str, Dict[str, Any]] = {}
    for contract, clause in rows:
        if contract.id not in contract_map:
            contract_map[contract.id] = {"contract": contract, "clauses": []}
        contract_map[contract.id]["clauses"].append(clause)

    all_violations = []
    for rule in rules:
        for cid, data in contract_map.items():
            contract = data["contract"]
            clauses = data["clauses"]
            matching = [c for c in clauses if c.clause_type == rule.rule_type]

            if rule.condition == "must_have" and not matching:
                all_violations.append({
                    "contract_id": contract.id,
                    "title": contract.title,
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "severity": rule.severity,
                    "reason": f"Missing required clause: {rule.rule_type}",
                })
            elif rule.condition == "max_value":
                threshold = _extract_number(rule.threshold_value)
                for cl in matching:
                    val = _extract_number(cl.clause_text)
                    if val is not None and threshold is not None and val > threshold:
                        all_violations.append({
                            "contract_id": contract.id,
                            "title": contract.title,
                            "rule_name": rule.rule_name,
                            "rule_type": rule.rule_type,
                            "severity": rule.severity,
                            "reason": f"Value {val} exceeds max threshold {threshold}",
                            "clause_text": cl.clause_text[:200],
                        })
            elif rule.condition == "min_value":
                threshold = _extract_number(rule.threshold_value)
                for cl in matching:
                    val = _extract_number(cl.clause_text)
                    if val is not None and threshold is not None and val < threshold:
                        all_violations.append({
                            "contract_id": contract.id,
                            "title": contract.title,
                            "rule_name": rule.rule_name,
                            "rule_type": rule.rule_type,
                            "severity": rule.severity,
                            "reason": f"Value {val} below min threshold {threshold}",
                            "clause_text": cl.clause_text[:200],
                        })

    return {
        "org_id": org_id,
        "rules_scanned": len(rules),
        "contracts_scanned": len(contract_map),
        "violations_found": len(all_violations),
        "violations": all_violations,
        "source": "sql",
    }


# ──────────────────────────── Pillar listing (for sidebar) ────────────────────────────

@router.get("/pillars/playbook")
async def list_playbook_pillars(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(PlaybookRule).where(PlaybookRule.org_id == org_id, PlaybookRule.is_active == True)
    )
    rules = result.scalars().all()
    return [
        {
            "id": r.id,
            "rule_name": r.rule_name,
            "rule_type": r.rule_type,
            "condition": r.condition,
            "threshold_value": r.threshold_value,
            "severity": r.severity,
        }
        for r in rules
    ]


@router.get("/pillars/statutes")
async def list_statute_pillars(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(EnforceabilityBenchmark))
    benchmarks = result.scalars().all()
    return [
        {
            "id": b.id,
            "statute_act": b.statute_act,
            "section_number": b.section_number,
            "clause_type": b.clause_type,
            "enforceability_score": b.enforceability_score,
            "conditions": b.conditions,
        }
        for b in benchmarks
    ]


@router.get("/pillars/regulations")
async def list_regulation_pillars(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(RegulatoryUpdate).order_by(RegulatoryUpdate.created_at.desc())
    )
    updates = result.scalars().all()
    return [
        {
            "id": u.id,
            "title": u.title,
            "source_id": u.source_id,
            "effective_date": u.effective_date,
            "affected_clause_types": u.affected_clause_types,
        }
        for u in updates
    ]


# ──────────────────────────── Visual Network Graph (SQL-derived) ────────────────────────────

# ──────────────────────────── Helpers ────────────────────────────

def _extract_number(text: str) -> float | None:
    """Extract the first numeric value from text."""
    if not text:
        return None
    # Look for currency/number patterns
    match = re.search(r"[₹$€£]?\s*([\d,]+(?:\.\d+)?)\s*(?:Cr|cr|L|l|lakhs?|crores?)?", text)
    if match:
        val_str = match.group(1).replace(",", "")
        try:
            val = float(val_str)
            # Normalize: if text has Cr/crore, multiply by 1e7 (to match INR convention in seed)
            lower = text.lower()
            if "cr" in lower or "crore" in lower:
                return val * 10000000
            if "l" in lower or "lak" in lower:
                return val * 100000
            return val
        except ValueError:
            return None
    return None
