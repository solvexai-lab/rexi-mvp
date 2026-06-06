"""
Network Graph router — unified 3-pillar graph for vis-network visualization.
Separated from knowledge_graph.py to avoid import cycles / duplicate endpoint issues.
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.get("/network")
async def get_network_graph(
    org_id: str = "demo-org",
    pillar: str = "all",
    session: AsyncSession = Depends(get_session),
):
    """Return a complete node/edge graph for vis-network visualization — built from PostgreSQL.
    
    pillar: all | playbook | law | regulatory
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen = set()

    def add_node(nid: str, label: str, group: str, value: int = 10, title: str = ""):
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "label": label, "group": group, "value": value, "title": title or label})

    # ── Raw SQL to avoid Pydantic v2 attribute-access pitfalls ──
    cres = await session.execute(
        text("SELECT id, title, contract_type, counterparty_name FROM contracts WHERE org_id = :org_id"),
        {"org_id": org_id}
    )
    contracts = [{"id": r[0], "title": r[1], "contract_type": r[2], "counterparty_name": r[3]} for r in cres.all()]
    cids = [c["id"] for c in contracts]

    clres = await session.execute(
        text("SELECT id, contract_id, clause_type, clause_text FROM contract_clauses WHERE contract_id = ANY(:cids)"),
        {"cids": cids}
    )
    clauses = [{"id": r[0], "contract_id": r[1], "clause_type": r[2], "clause_text": r[3]} for r in clres.all()]

    # Filter clauses by pillar relevance
    if pillar == "playbook":
        rres = await session.execute(
            text("SELECT id, rule_name, rule_type, condition, threshold_value, severity FROM playbook_rules WHERE org_id = :org_id AND is_active = true"),
            {"org_id": org_id}
        )
        rules = [{"id": r[0], "rule_name": r[1], "rule_type": r[2], "condition": r[3], "threshold_value": r[4], "severity": r[5]} for r in rres.all()]
        relevant_clause_types = {r["rule_type"] for r in rules}
        clauses = [cl for cl in clauses if cl["clause_type"] in relevant_clause_types]
        benchmarks = []
        alerts = []
    elif pillar == "law":
        rules = []
        bres = await session.execute(
            text("SELECT id, clause_type, statute_act, section_number, enforceability_score, conditions FROM enforceability_benchmarks")
        )
        benchmarks = [{"id": r[0], "clause_type": r[1], "statute_act": r[2], "section_number": r[3], "enforceability_score": r[4], "conditions": r[5]} for r in bres.all()]
        relevant_clause_types = {bm["clause_type"] for bm in benchmarks}
        clauses = [cl for cl in clauses if cl["clause_type"] in relevant_clause_types]
        alerts = []
    elif pillar == "regulatory":
        rules = []
        benchmarks = []
        clauses = []  # Regulatory graph: contracts -> alerts directly
        ares = await session.execute(
            text("SELECT id, title, priority, description, affected_contract_ids FROM regulatory_alerts WHERE org_id = :org_id"),
            {"org_id": org_id}
        )
        alerts = [{"id": r[0], "title": r[1], "priority": r[2], "description": r[3], "affected_contract_ids": r[4] or []} for r in ares.all()]
    else:
        rres = await session.execute(
            text("SELECT id, rule_name, rule_type, condition, threshold_value, severity FROM playbook_rules WHERE org_id = :org_id AND is_active = true"),
            {"org_id": org_id}
        )
        rules = [{"id": r[0], "rule_name": r[1], "rule_type": r[2], "condition": r[3], "threshold_value": r[4], "severity": r[5]} for r in rres.all()]
        bres = await session.execute(
            text("SELECT id, clause_type, statute_act, section_number, enforceability_score, conditions FROM enforceability_benchmarks")
        )
        benchmarks = [{"id": r[0], "clause_type": r[1], "statute_act": r[2], "section_number": r[3], "enforceability_score": r[4], "conditions": r[5]} for r in bres.all()]
        ares = await session.execute(
            text("SELECT id, title, priority, description, affected_contract_ids FROM regulatory_alerts WHERE org_id = :org_id"),
            {"org_id": org_id}
        )
        alerts = [{"id": r[0], "title": r[1], "priority": r[2], "description": r[3], "affected_contract_ids": r[4] or []} for r in ares.all()]

    # ── Build nodes ──
    for c in contracts:
        add_node(
            f"c-{c['id']}",
            (c['title'][:28] + '...') if len(c['title']) > 28 else c['title'],
            "contract",
            20,
            f"{c['title']}\nType: {c['contract_type']}\nCounterparty: {c['counterparty_name']}"
        )

    for cl in clauses:
        add_node(f"cl-{cl['id']}", cl['clause_type'][:20], "clause", 8,
                 f"{cl['clause_type']}\n{cl['clause_text'][:180]}")
        edges.append({"from": f"c-{cl['contract_id']}", "to": f"cl-{cl['id']}",
                      "label": "has", "arrows": "to", "color": {"color": "#CBD5E1"}})

    for r in rules:
        add_node(f"r-{r['id']}",
                 (r['rule_name'][:30] + '...') if len(r['rule_name']) > 30 else r['rule_name'],
                 "rule_ok", 12,
                 f"{r['rule_name']}\n{r['rule_type']} | {r['condition']} {r['threshold_value']}")
        for cl in clauses:
            if cl['clause_type'] == r['rule_type']:
                edges.append({"from": f"cl-{cl['id']}", "to": f"r-{r['id']}",
                              "label": "checked_by", "arrows": "to", "color": {"color": "#22C55E"}})

    for bm in benchmarks:
        is_risk = bm['enforceability_score'] < 0.75
        add_node(f"b-{bm['id']}", f"{bm['statute_act'][:22]}...",
                 "statute_risk" if is_risk else "statute_ok", 10,
                 f"{bm['statute_act']} {bm['section_number']}\nScore: {bm['enforceability_score']}")
        for cl in clauses:
            if cl['clause_type'] == bm['clause_type']:
                edges.append({"from": f"cl-{cl['id']}", "to": f"b-{bm['id']}",
                              "label": "governed_by", "arrows": "to",
                              "color": {"color": "#F59E0B" if is_risk else "#3B82F6"}})

    for al in alerts:
        add_node(f"a-{al['id']}",
                 (al['title'][:30] + '...') if len(al['title']) > 30 else al['title'],
                 "regulation", 14,
                 f"{al['title']}\nPriority: {al['priority']}")
        for aff in al['affected_contract_ids']:
            edges.append({"from": f"c-{aff}", "to": f"a-{al['id']}",
                          "label": "affected", "arrows": "to", "color": {"color": "#EF4444"}})

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {"contracts": len(contracts), "clauses": len(clauses), "rules": len(rules), "statutes": len(benchmarks), "regulations": len(alerts)},
        "source": "sql",
    }
