"""Intelligent context builder for contract Q&A.

Retrieval hierarchy:
  1. PageIndex tree query (structure-aware, most precise)
  2. Embedding similarity search (semantic, broad coverage)
  3. Clause dump fallback (deterministic, always works)

Each layer is wrapped with graceful degradation so the chat never breaks.
"""
import os
import math
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.tables import Contract, ContractClause, ContractEmbedding, ContractTreeIndex
from app.services.pageindex_service import pageindex_service

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MAX_CONTEXT_TOKENS = 6000  # Rough token budget for context
MAX_CLAUSE_CHARS = 800    # Per-clause character limit


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return len(text) // 4


def _active_embedder() -> str:
    if GEMINI_API_KEY:
        return "gemini"
    if OPENAI_API_KEY:
        return "openai"
    return "hash"


async def _get_embedding(text: str) -> Tuple[List[float], str]:
    """Generate embedding for query text."""
    name = _active_embedder()
    if name == "gemini":
        import httpx
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"
        async with httpx.AsyncClient() as client:
            r = await client.post(
                url, params={"key": GEMINI_API_KEY},
                json={"content": {"parts": [{"text": text[:8000]}]}},
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["embedding"]["values"], name
    if name == "openai":
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"input": text[:8000], "model": "text-embedding-3-small"},
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["data"][0]["embedding"], name
    # Hash fallback
    from backend.indexing.embedder import HashEmbedder
    embedder = HashEmbedder(dims=128)
    return embedder.embed_query(text), name


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0


class ChatContextService:
    """Builds optimized context for contract Q&A with multi-tier retrieval."""

    async def build_context(
        self,
        contract_id: str,
        question: str,
        session: AsyncSession,
    ) -> Dict:
        """Build context dict with text, sources, and retrieval metadata."""
        result = await session.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            return {"text": "", "sources": [], "method": "none", "error": "Contract not found"}

        header = f"Contract: {contract.title}\nCounterparty: {contract.counterparty_name}\nGoverning Law: {contract.governing_law}\n\n"

        # Tier 1: PageIndex tree query (most precise)
        tree_context = await self._retrieve_from_tree(contract_id, question, session)
        if tree_context["text"]:
            return {
                "text": header + tree_context["text"],
                "sources": tree_context["sources"],
                "method": "pageindex",
                "nodes_found": len(tree_context["sources"]),
            }

        # Tier 2: Embedding similarity search
        emb_context = await self._retrieve_from_embeddings(contract_id, question, session)
        if emb_context["text"]:
            return {
                "text": header + emb_context["text"],
                "sources": emb_context["sources"],
                "method": "embeddings",
                "chunks_found": len(emb_context["sources"]),
            }

        # Tier 3: All clauses fallback (deterministic)
        clause_context = await self._retrieve_all_clauses(contract_id, session)
        return {
            "text": header + clause_context["text"],
            "sources": clause_context["sources"],
            "method": "clauses",
            "clauses_found": len(clause_context["sources"]),
        }

    async def _retrieve_from_tree(
        self, contract_id: str, question: str, session: AsyncSession
    ) -> Dict:
        """Query PageIndex tree for relevant sections."""
        try:
            result = await session.execute(
                select(ContractTreeIndex).where(ContractTreeIndex.contract_id == contract_id)
            )
            tree_row = result.scalar_one_or_none()
            if not tree_row or not tree_row.structure:
                return {"text": "", "sources": []}

            tree_data = {"structure": tree_row.structure}
            matches = pageindex_service.query_tree(tree_data, question)
            if not matches:
                return {"text": "", "sources": []}

            # Take top matches up to token budget
            sources = []
            context_parts = []
            total_chars = 0
            max_chars = MAX_CONTEXT_TOKENS * 4

            for match in matches[:5]:
                text = match.get("text_preview", "") or ""
                if len(text) > MAX_CLAUSE_CHARS:
                    text = text[:MAX_CLAUSE_CHARS] + "..."
                if total_chars + len(text) > max_chars:
                    break
                total_chars += len(text)
                context_parts.append(f"[{match['title']}]\n{text}\n")
                sources.append({
                    "type": "tree_node",
                    "title": match["title"],
                    "node_id": match.get("node_id", ""),
                    "score": match.get("score", 0),
                })

            return {"text": "\n".join(context_parts), "sources": sources}
        except Exception:
            return {"text": "", "sources": []}

    async def _retrieve_from_embeddings(
        self, contract_id: str, question: str, session: AsyncSession
    ) -> Dict:
        """Semantic search over clause embeddings."""
        try:
            query_emb, emb_name = await _get_embedding(question)
        except Exception:
            return {"text": "", "sources": []}

        try:
            result = await session.execute(
                select(ContractEmbedding).where(
                    ContractEmbedding.contract_id == contract_id,
                    ContractEmbedding.embedder == emb_name,
                )
            )
            all_embs = result.scalars().all()
            if not all_embs:
                return {"text": "", "sources": []}

            scored = [(ce, _cosine_similarity(query_emb, ce.embedding)) for ce in all_embs if ce.embedding]
            scored.sort(key=lambda x: x[1], reverse=True)

            sources = []
            context_parts = []
            total_chars = 0
            max_chars = MAX_CONTEXT_TOKENS * 4

            for ce, score in scored[:5]:
                text = ce.chunk_text or ""
                if len(text) > MAX_CLAUSE_CHARS:
                    text = text[:MAX_CLAUSE_CHARS] + "..."
                if total_chars + len(text) > max_chars:
                    break
                total_chars += len(text)
                context_parts.append(f"[Clause on page {ce.page_number}]\n{text}\n")
                sources.append({
                    "type": "embedding",
                    "page_number": ce.page_number,
                    "score": round(score, 4),
                })

            return {"text": "\n".join(context_parts), "sources": sources}
        except Exception:
            return {"text": "", "sources": []}

    async def _retrieve_all_clauses(
        self, contract_id: str, session: AsyncSession
    ) -> Dict:
        """Fallback: dump all clauses up to token budget."""
        try:
            result = await session.execute(
                select(ContractClause).where(ContractClause.contract_id == contract_id)
            )
            clauses = result.scalars().all()

            sources = []
            context_parts = []
            total_chars = 0
            max_chars = MAX_CONTEXT_TOKENS * 4

            for cl in clauses:
                text = cl.clause_text[:MAX_CLAUSE_CHARS]
                if len(cl.clause_text) > MAX_CLAUSE_CHARS:
                    text += "..."
                snippet = f"[{cl.clause_type}] (page {cl.page_number})\n{text}\n"
                if total_chars + len(snippet) > max_chars:
                    break
                total_chars += len(snippet)
                context_parts.append(snippet)
                sources.append({
                    "type": "clause",
                    "clause_type": cl.clause_type,
                    "page_number": cl.page_number,
                })

            return {"text": "\n".join(context_parts), "sources": sources}
        except Exception:
            return {"text": "", "sources": []}


chat_context_service = ChatContextService()
