"""Tests for PageIndex document tree builder."""
import pytest
from fastapi.testclient import TestClient
from app.services.pageindex_service import PageIndexService, pageindex_service
from app.main import app

client = TestClient(app)

SAMPLE_MARKDOWN = """# Master Services Agreement

This agreement is between Vendor Corp and Client Inc.

## 1. Scope of Services

Vendor Corp shall provide software development services.

### 1.1 Development

All code shall be delivered according to specifications.

### 1.2 Testing

Quality assurance shall be performed before delivery.

## 2. Payment Terms

Payment shall be made within 30 days of invoice.

### 2.1 Invoicing

Invoices shall be submitted monthly.

### 2.2 Late Fees

Late payments subject to 1.5% monthly fee.

## 3. Termination

Either party may terminate with 30 days notice.
"""


# ── Service Unit Tests ──

def test_status():
    status = pageindex_service.status()
    assert "enabled" in status
    assert "gemini_available" in status


def test_build_tree_from_markdown():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, doc_name="test_contract.md", add_summaries=False
    )
    assert result["doc_name"] == "test_contract.md"
    assert result["line_count"] > 0
    assert len(result["structure"]) > 0


def test_tree_has_correct_hierarchy():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, add_summaries=False
    )
    structure = result["structure"]
    # Root should have "Master Services Agreement"
    assert structure[0]["title"] == "Master Services Agreement"
    # Should have children for sections 1, 2, 3
    top_nodes = [n["title"] for n in structure[0].get("nodes", [])]
    assert "1. Scope of Services" in top_nodes
    assert "2. Payment Terms" in top_nodes
    assert "3. Termination" in top_nodes


def test_node_ids_assigned():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, add_summaries=False
    )

    def check_ids(nodes):
        for node in nodes:
            assert node.get("node_id", "") != ""
            if "nodes" in node:
                check_ids(node["nodes"])

    check_ids(result["structure"])


def test_flatten_tree():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, add_summaries=False
    )
    flat = pageindex_service.flatten_tree(result)
    assert len(flat) > 0
    titles = [n["title"] for n in flat]
    assert "Master Services Agreement" in titles
    assert "1. Scope of Services" in titles
    assert "2. Payment Terms" in titles


def test_query_tree():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, add_summaries=False
    )
    results = pageindex_service.query_tree(result, "payment late fee")
    assert len(results) > 0
    titles = [r["title"] for r in results]
    assert any("Payment" in t or "Late" in t for t in titles)


def test_query_tree_no_match():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, add_summaries=False
    )
    results = pageindex_service.query_tree(result, "xyznonexistent")
    assert len(results) == 0


def test_empty_markdown():
    result = pageindex_service.build_tree_from_markdown("", add_summaries=False)
    assert result["structure"] == []
    assert result["line_count"] == 0


def test_markdown_no_headers():
    result = pageindex_service.build_tree_from_markdown(
        "This is just plain text with no headers.", add_summaries=False
    )
    assert result["structure"] == []


def test_build_tree_preserves_text():
    result = pageindex_service.build_tree_from_markdown(
        SAMPLE_MARKDOWN, add_summaries=False
    )
    # Find the payment terms node
    payment_node = None
    for node in result["structure"][0].get("nodes", []):
        if "Payment" in node["title"]:
            payment_node = node
            break
    assert payment_node is not None
    assert "30 days" in payment_node.get("text", "")


# ── API Endpoint Tests ──

def test_api_status():
    response = client.get("/api/v1/pageindex/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data


def test_api_get_tree_not_found():
    response = client.get("/api/v1/pageindex/contracts/nonexistent/tree")
    assert response.status_code == 404


def test_api_flatten_not_found():
    response = client.get("/api/v1/pageindex/contracts/nonexistent/flatten")
    assert response.status_code == 404


def test_api_query_not_found():
    response = client.post(
        "/api/v1/pageindex/contracts/nonexistent/query",
        json={"query": "payment"}
    )
    assert response.status_code == 404


# ── Service Instance Tests ──

def test_service_singleton():
    assert pageindex_service is not None
    assert isinstance(pageindex_service, PageIndexService)
