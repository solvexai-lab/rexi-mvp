"""Integration tests for Day 1 + Day 2 features.
Uses in-memory SQLite via conftest fixtures.
"""
import pytest
from sqlmodel import select
from app.models.tables import Contract, ContractClause, ContractVersion


# ──────────────────────────── Day 2: Counterparty ────────────────────────────

@pytest.mark.asyncio
async def test_counterparty_dashboard_empty(client):
    """Counterparty dashboard returns empty list when no contracts."""
    resp = await client.get("/api/v1/counterparties/dashboard?org_id=test-org")
    assert resp.status_code == 200
    data = resp.json()
    assert data["org_id"] == "test-org"
    assert data["counterparties"] == []


@pytest.mark.asyncio
async def test_counterparty_dashboard_with_contracts(client, db_session):
    """Counterparty dashboard aggregates risk per vendor deterministically."""
    # Seed contracts with counterparties
    c1 = Contract(id="c1", org_id="demo-org", title="MSA Alpha", counterparty_name="VendorX",
                  contract_type="MSA", status="active", value_inr=5_000_000)
    c2 = Contract(id="c2", org_id="demo-org", title="SOW Beta", counterparty_name="VendorX",
                  contract_type="SOW", status="active", value_inr=2_000_000)
    c3 = Contract(id="c3", org_id="demo-org", title="MSA Gamma", counterparty_name="VendorY",
                  contract_type="MSA", status="active", value_inr=10_000_000)
    db_session.add_all([c1, c2, c3])
    await db_session.commit()

    resp = await client.get("/api/v1/counterparties/dashboard?org_id=demo-org")
    assert resp.status_code == 200
    data = resp.json()

    cps = {cp["name"]: cp for cp in data["counterparties"]}
    assert "VendorX" in cps
    assert "VendorY" in cps

    # VendorX: 2 contracts, 7M value
    vx = cps["VendorX"]
    assert vx["contract_count"] == 2
    assert vx["total_value_inr"] == 7_000_000

    # VendorY: 1 contract, 10M value
    vy = cps["VendorY"]
    assert vy["contract_count"] == 1
    assert vy["total_value_inr"] == 10_000_000


@pytest.mark.asyncio
async def test_counterparty_contracts_list(client, db_session):
    """List contracts for a specific counterparty."""
    c1 = Contract(id="c1", org_id="demo-org", title="MSA Alpha", counterparty_name="VendorX",
                  contract_type="MSA", status="active", value_inr=5_000_000)
    db_session.add(c1)
    await db_session.commit()

    resp = await client.get("/api/v1/counterparties/VendorX/contracts?org_id=demo-org")
    assert resp.status_code == 200
    data = resp.json()
    assert data["counterparty_name"] == "VendorX"
    assert len(data["contracts"]) == 1
    assert data["contracts"][0]["title"] == "MSA Alpha"


# ──────────────────────────── Day 2: Contract Versions ────────────────────────────

@pytest.mark.asyncio
async def test_list_contract_versions_empty(client, db_session):
    """Versions endpoint returns empty list for contract with no versions."""
    c1 = Contract(id="c1", org_id="demo-org", title="Test", counterparty_name="V",
                  contract_type="MSA", status="active", value_inr=0)
    db_session.add(c1)
    await db_session.commit()

    resp = await client.get("/api/v1/redline/contracts/c1/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_id"] == "c1"
    assert data["versions"] == []


@pytest.mark.asyncio
async def test_list_contract_versions_populated(client, db_session):
    """Versions endpoint returns stored versions sorted by version_number desc."""
    c1 = Contract(id="c1", org_id="demo-org", title="Test", counterparty_name="V",
                  contract_type="MSA", status="active", value_inr=0)
    v1 = ContractVersion(id="v1", contract_id="c1", version_number=1, title="Draft")
    v2 = ContractVersion(id="v2", contract_id="c1", version_number=2, title="Final")
    db_session.add_all([c1, v1, v2])
    await db_session.commit()

    resp = await client.get("/api/v1/redline/contracts/c1/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["versions"]) == 2
    assert data["versions"][0]["version_number"] == 2
    assert data["versions"][0]["title"] == "Final"
    assert data["versions"][1]["version_number"] == 1


# ──────────────────────────── Day 1: Redline ────────────────────────────

@pytest.mark.asyncio
async def test_redline_compare_contracts_not_found(client):
    """Redline compare returns 404 if either contract missing."""
    resp = await client.get("/api/v1/redline/contracts/missing/compare/also-missing")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_redline_compare_contracts_success(client, db_session):
    """Semantic diff between two contracts with clauses."""
    c1 = Contract(id="c1", org_id="demo-org", title="A", counterparty_name="V",
                  contract_type="MSA", status="active", value_inr=0)
    c2 = Contract(id="c2", org_id="demo-org", title="B", counterparty_name="V",
                  contract_type="MSA", status="active", value_inr=0)
    cl1 = ContractClause(id="cl1", contract_id="c1", clause_type="termination", clause_text="30 days notice")
    cl2 = ContractClause(id="cl2", contract_id="c2", clause_type="termination", clause_text="60 days notice required")
    db_session.add_all([c1, c2, cl1, cl2])
    await db_session.commit()

    resp = await client.get("/api/v1/redline/contracts/c1/compare/c2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_a"] == "c1"
    assert data["contract_b"] == "c2"
    assert len(data["comparison"]) >= 1
    comp = data["comparison"][0]
    assert "label" in comp
    assert "similarity_score" in comp


@pytest.mark.asyncio
async def test_redline_clauses_compare(client):
    """Direct clause text comparison."""
    payload = {
        "old_text": "The vendor shall deliver within 30 days.",
        "new_text": "The vendor may deliver within 60 days.",
    }
    resp = await client.post("/api/v1/redline/clauses/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "label" in data
    assert "change_summary" in data
    assert "key_differences" in data


@pytest.mark.asyncio
async def test_redline_what_if(client):
    """What-if scenario returns structured result."""
    payload = {
        "original_clause": "Vendor pays 1000 within 30 days.",
        "proposed_clause": "Vendor pays 500 within 60 days.",
        "playbook_standard": "Standard payment terms: 1000 within 30 days.",
    }
    # This calls Gemini — skip in CI if no API key
    import os
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
    resp = await client.post("/api/v1/redline/what-if", json=payload)
    # Gemini may return 503 if API is unavailable even with key set
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, dict)


# ──────────────────────────── Day 1: Plain English ────────────────────────────

@pytest.mark.asyncio
async def test_plain_english_list_empty(client, db_session):
    """Plain English list returns empty when no summaries exist.
    Skips if no Gemini key since endpoint auto-generates.
    """
    import os
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")

    c1 = Contract(id="c1", org_id="demo-org", title="Test", counterparty_name="V",
                  contract_type="MSA", status="active", value_inr=0)
    cl1 = ContractClause(id="cl1", contract_id="c1", clause_type="termination", clause_text="30 days notice")
    db_session.add_all([c1, cl1])
    await db_session.commit()

    resp = await client.get("/api/v1/plain-english/contracts/c1")
    assert resp.status_code in (200, 400, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert data.get("contract_id") == "c1"


# ──────────────────────────── Day 2: GraphRAG Service Imports ────────────────────────────

def test_graphrag_cypher_imports():
    """All literal copies from vendor repos import cleanly."""
    from app.services.graphrag_cypher import (
        CREATE_GRAPH_STATEMENT,
        CREATE_VECTOR_INDEX_STATEMENT,
        CREATE_FULL_TEXT_INDICES,
        EMBEDDINGS_STATEMENT,
        NEO4J_SCHEMA,
        ContractSearchService,
        create_full_text_indices,
    )
    assert len(CREATE_GRAPH_STATEMENT) > 500
    assert "MERGE (agreement:Agreement" in CREATE_GRAPH_STATEMENT
    assert "vector.dimensions" in CREATE_VECTOR_INDEX_STATEMENT
    assert "Excerpt" in NEO4J_SCHEMA


def test_docx_diff_imports():
    """Legal-redline diff imports cleanly from vendor repo."""
    from legal_redline.diff import diff_documents
    from legal_redline.compare import compare_agreements, format_comparison_report
    assert callable(diff_documents)
    assert callable(compare_agreements)


def test_semantic_diff_imports():
    """Multi-agent-contract clause compare imports cleanly."""
    from app.services.semantic_diff import (
        ClauseComparisonAgent, ClauseCompareResult, _diff_bullets, _numbers
    )
    bullets = _diff_bullets("pay 1000 within 30 days", "pay 500 within 60 days")
    assert isinstance(bullets, list)
    nums = _numbers("Section 12 and 34A")
    assert isinstance(nums, list)
