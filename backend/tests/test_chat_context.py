"""Tests for intelligent chat context retrieval (PageIndex + embeddings + fallback)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat_context_service import ChatContextService, _cosine_similarity


class MockClause:
    def __init__(self, clause_type, clause_text, page_number=1):
        self.clause_type = clause_type
        self.clause_text = clause_text
        self.page_number = page_number


class MockContract:
    def __init__(self, title="Test Contract", counterparty_name="Vendor", governing_law="India"):
        self.title = title
        self.counterparty_name = counterparty_name
        self.governing_law = governing_law


class MockTreeRow:
    def __init__(self, structure):
        self.structure = structure


class MockEmbedding:
    def __init__(self, contract_id, chunk_text, embedding, page_number, embedder):
        self.contract_id = contract_id
        self.chunk_text = chunk_text
        self.embedding = embedding
        self.page_number = page_number
        self.embedder = embedder


@pytest.mark.asyncio
async def test_build_context_with_tree():
    """When tree exists, should use PageIndex retrieval."""
    service = ChatContextService()

    # Mock session
    mock_session = MagicMock()
    mock_contract = MockContract()
    mock_tree = MockTreeRow([
        {"title": "Payment Terms", "node_id": "1", "text": "Payment within 30 days", "nodes": []}
    ])

    # Setup execute chain for contract query
    exec_contract = MagicMock()
    exec_contract.scalar_one_or_none.return_value = mock_contract

    # Setup execute chain for tree query
    exec_tree = MagicMock()
    exec_tree.scalar_one_or_none.return_value = mock_tree

    mock_session.execute = AsyncMock(side_effect=[exec_contract, exec_tree])

    result = await service.build_context("c1", "payment terms", mock_session)

    assert result["method"] == "pageindex"
    assert "Payment Terms" in result["text"]
    assert len(result["sources"]) > 0


@pytest.mark.asyncio
async def test_build_context_no_tree_falls_back_to_clauses():
    """When no tree and no embeddings, should fall back to all clauses."""
    service = ChatContextService()

    mock_session = MagicMock()
    mock_contract = MockContract()
    mock_clause = MockClause("TERMINATION", "Either party may terminate with 30 days notice.")

    # Contract exists, no tree, no embeddings, clauses found
    exec_contract = MagicMock()
    exec_contract.scalar_one_or_none.return_value = mock_contract

    exec_tree = MagicMock()
    exec_tree.scalar_one_or_none.return_value = None

    exec_embeddings = MagicMock()
    exec_embeddings.scalars.return_value.all.return_value = []

    exec_clauses = MagicMock()
    exec_clauses.scalars.return_value.all.return_value = [mock_clause]

    mock_session.execute = AsyncMock(side_effect=[exec_contract, exec_tree, exec_embeddings, exec_clauses])

    # Patch _get_embedding to avoid external API calls
    with patch('app.services.chat_context_service._get_embedding', return_value=([0.1, 0.2], 'test')):
        result = await service.build_context("c1", "termination clause", mock_session)

    assert result["method"] == "clauses"
    assert "TERMINATION" in result["text"]


@pytest.mark.asyncio
async def test_build_context_contract_not_found():
    """When contract doesn't exist, return empty context with error."""
    service = ChatContextService()

    mock_session = MagicMock()
    exec_contract = MagicMock()
    exec_contract.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=exec_contract)

    result = await service.build_context("nonexistent", "question", mock_session)

    assert result["method"] == "none"
    assert "error" in result


@pytest.mark.asyncio
async def test_build_context_empty_tree():
    """When tree exists but is empty, should fall back."""
    service = ChatContextService()

    mock_session = MagicMock()
    mock_contract = MockContract()
    mock_tree = MockTreeRow([])
    mock_clause = MockClause("SCOPE", "Vendor shall provide services.")

    exec_contract = MagicMock()
    exec_contract.scalar_one_or_none.return_value = mock_contract

    exec_tree = MagicMock()
    exec_tree.scalar_one_or_none.return_value = mock_tree

    exec_clauses = MagicMock()
    exec_clauses.scalars.return_value.all.return_value = [mock_clause]

    mock_session.execute = AsyncMock(side_effect=[exec_contract, exec_tree, exec_clauses])

    result = await service.build_context("c1", "scope", mock_session)

    assert result["method"] == "clauses"


def test_cosine_similarity():
    """Cosine similarity should be 1.0 for identical vectors."""
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert _cosine_similarity(a, b) == 1.0


def test_cosine_similarity_orthogonal():
    """Cosine similarity should be 0.0 for orthogonal vectors."""
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert _cosine_similarity(a, b) == 0.0


def test_cosine_similarity_empty():
    """Cosine similarity should be 0.0 for zero vectors."""
    a = [0.0, 0.0]
    b = [1.0, 0.0]
    assert _cosine_similarity(a, b) == 0.0
