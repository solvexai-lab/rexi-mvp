"""Contract embedding router — vector search over contract chunks.

Embedder priority:
  1. Gemini embedding-001 (free tier, 3072-dim) — uses GEMINI_API_KEY
  2. OpenAI text-embedding-3-small (1536-dim) — uses OPENAI_API_KEY
  3. agentic-rag HashEmbedder (128-dim, deterministic, zero cost) — fallback

Embeddings are tagged with their embedder name so searches never mix dimensions.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from app.core.database import get_session
from app.models.tables import Contract, ContractEmbedding
from app.services.langfuse_service import langfuse_observer

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Embedder selection ---
_hash_embedder = None


def _get_fallback_embedder():
    global _hash_embedder
    if _hash_embedder is None:
        from backend.indexing.embedder import HashEmbedder
        _hash_embedder = HashEmbedder(dims=128)
    return _hash_embedder


async def _gemini_embed(text: str) -> List[float]:
    import httpx
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            url, params={"key": GEMINI_API_KEY},
            json={"content": {"parts": [{"text": text[:8000]}]}},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["embedding"]["values"]


async def _openai_embed(text: str) -> List[float]:
    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"input": text[:8000], "model": "text-embedding-3-small"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]


def _hash_embed(text: str) -> List[float]:
    return _get_fallback_embedder().embed_query(text)


def _active_embedder() -> str:
    if GEMINI_API_KEY:
        return "gemini"
    if OPENAI_API_KEY:
        return "openai"
    return "hash"


async def _get_embedding(text: str) -> tuple[List[float], str]:
    """Return (embedding_vector, embedder_name)."""
    name = _active_embedder()
    if name == "gemini":
        return await _gemini_embed(text), name
    if name == "openai":
        return await _openai_embed(text), name
    return _hash_embed(text), name


@router.post("/contracts/{contract_id}/index")
@langfuse_observer(name="embeddings.index")
async def index_contract_chunks(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Generate and store embeddings for all clauses in a contract."""
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    from app.models.tables import ContractClause
    res = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
    clauses = res.scalars().all()

    indexed = 0
    for cl in clauses:
        existing = await session.execute(
            select(ContractEmbedding).where(
                ContractEmbedding.contract_id == contract_id,
                ContractEmbedding.chunk_text == cl.clause_text[:500],
            )
        )
        if existing.scalar_one_or_none():
            continue

        try:
            emb, emb_name = await _get_embedding(cl.clause_text)
            ce = ContractEmbedding(
                contract_id=contract_id,
                chunk_text=cl.clause_text[:500],
                embedding=emb,
                page_number=cl.page_number,
                embedder=emb_name,
            )
            session.add(ce)
            indexed += 1
        except Exception:
            continue

    await session.commit()
    return {
        "contract_id": contract_id,
        "indexed_chunks": indexed,
        "embedder": _active_embedder(),
    }


@router.post("/search")
@langfuse_observer(name="embeddings.search")
async def search_embeddings(query: dict, session: AsyncSession = Depends(get_session)):
    """Semantic search over contract embeddings using cosine similarity.
    Only searches embeddings from the currently active embedder to avoid dimension mismatch.
    """
    q = query.get("query", "")
    top_k = query.get("top_k", 5)
    if not q:
        raise HTTPException(status_code=400, detail="Query required")

    try:
        query_emb, emb_name = await _get_embedding(q)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding generation failed: {str(e)}")

    result = await session.execute(
        select(ContractEmbedding).where(ContractEmbedding.embedder == emb_name)
    )
    all_embs = result.scalars().all()

    import math

    def cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0

    scored = [(ce, cosine_similarity(query_emb, ce.embedding)) for ce in all_embs if ce.embedding]
    scored.sort(key=lambda x: x[1], reverse=True)

    return {
        "query": q,
        "embedder": emb_name,
        "results": [
            {
                "contract_id": ce.contract_id,
                "chunk_text": ce.chunk_text,
                "page_number": ce.page_number,
                "score": round(score, 4),
            }
            for ce, score in scored[:top_k]
        ],
    }
