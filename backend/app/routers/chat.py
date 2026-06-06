"""Chat with Contracts router — adapted from agentic-rag streaming patterns.
Supports SSE streaming for real-time token delivery.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.database import get_session
from app.models.tables import Contract, ContractClause
from app.services.gemini_service import chat_answer, stream_chat_answer, GeminiUnavailableError
from app.services.langfuse_service import langfuse_observer, trace_generation, get_langfuse
from app.services.chat_context_service import chat_context_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _sse(event: str, data: dict) -> str:
    """Format data as Server-Sent Event. Copied from agentic-rag."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _build_fallback_answer(question: str, context_result: dict) -> str:
    """Build a helpful fallback answer when the LLM is unavailable.
    Uses retrieved context sources to provide relevant contract excerpts.
    """
    lines = [
        "🤖 REXI Fallback (AI assistant is currently unavailable)",
        "",
        f"Your question: \"{question}\"",
        "",
        "Here are the most relevant contract sections based on your query:",
        "",
    ]

    sources = context_result.get("sources", [])
    context_text = context_result.get("text", "")

    if sources:
        for i, src in enumerate(sources[:5], 1):
            title = src.get("title", "Section")
            text = src.get("text", "")
            if text:
                lines.append(f"{i}. {title}")
                lines.append(f"   {text[:400]}{'...' if len(text) > 400 else ''}")
                lines.append("")
    elif context_text:
        lines.append(context_text[:2000])
    else:
        lines.append("No specific sections were found for this question. Try asking about specific clauses like termination, payment, liability, or confidentiality.")

    lines.append("")
    lines.append("—")
    lines.append("Tip: Configure GEMINI_API_KEY to enable AI-powered answers.")
    return "\n".join(lines)


@router.post("/contracts/{contract_id}/ask")
@langfuse_observer(name="chat.ask_contract")
async def ask_contract(contract_id: str, data: dict, session: AsyncSession = Depends(get_session)):
    """Non-streaming Q&A about a specific contract."""
    question = data.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question required")

    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Intelligent context retrieval: PageIndex tree → embeddings → clauses
    context_result = await chat_context_service.build_context(contract_id, question, session)
    context = context_result["text"]

    try:
        answer = await chat_answer(question, context)
    except GeminiUnavailableError:
        # Graceful fallback: return retrieved context with a helpful message
        answer = _build_fallback_answer(question, context_result)
    return {
        "contract_id": contract_id,
        "question": question,
        "answer": answer,
        "retrieval_method": context_result.get("method", "unknown"),
        "sources": context_result.get("sources", []),
        "fallback": "AI assistant is currently unavailable. Showing relevant contract excerpts instead." if "REXI Fallback" in answer else None,
    }


@router.post("/contracts/{contract_id}/ask/stream")
async def ask_contract_stream(contract_id: str, data: dict, session: AsyncSession = Depends(get_session)):
    """Streaming Q&A about a contract via SSE.
    Adapted from agentic-rag backend/querying/stream.py.
    """
    question = data.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question required")

    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Intelligent context retrieval
    context_result = await chat_context_service.build_context(contract_id, question, session)
    context = context_result["text"]
    retrieval_method = context_result.get("method", "unknown")

    async def event_generator():
        # Langfuse manual trace for streaming
        lf = get_langfuse()
        trace = None
        generation = None
        if lf:
            trace = lf.trace(name="chat.ask_contract_stream", input={"question": question, "contract_id": contract_id})
            generation = trace.generation(name="gemini-stream", model="gemini-2.0-flash", input=question)

        yield _sse("step", {"type": "analyzing", "title": "Analyzing question", "description": "Understanding your query..."})
        method_desc = {
            "pageindex": "Searching document structure (PageIndex)...",
            "embeddings": "Searching semantic embeddings...",
            "clauses": "Scanning contract clauses...",
        }.get(retrieval_method, "Searching contract...")
        yield _sse("step", {"type": "searching", "title": "Searching contract", "description": method_desc})
        yield _sse("step", {"type": "generating", "title": "Generating answer", "description": "Synthesizing response..."})

        full_answer = ""
        try:
            async for token in stream_chat_answer(question, context):
                full_answer += token
                yield _sse("token", {"token": token})
        except GeminiUnavailableError as e:
            if generation:
                generation.end(output={"error": str(e)})
            # Graceful fallback: stream the fallback answer as tokens
            fallback = _build_fallback_answer(question, {"text": context, "sources": context_result.get("sources", [])})
            yield _sse("step", {"type": "fallback", "title": "AI unavailable", "description": "Showing relevant contract excerpts instead..."})
            # Stream fallback in chunks for UX
            for chunk in fallback.split("\n"):
                yield _sse("token", {"token": chunk + "\n"})
            yield _sse("complete", {"answer": fallback, "fallback": True})
            return

        if generation:
            generation.end(output=full_answer)
        yield _sse("complete", {"answer": full_answer})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/portfolio/ask")
@langfuse_observer(name="chat.ask_portfolio")
async def ask_portfolio(data: dict, session: AsyncSession = Depends(get_session)):
    """Q&A across all contracts in an org."""
    org_id = data.get("org_id", "demo-org")
    question = data.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question required")

    result = await session.execute(select(Contract).where(Contract.org_id == org_id))
    contracts = result.scalars().all()

    # Build context from all contracts (limit to avoid token overflow)
    context = f"Organization: {org_id}\nTotal contracts: {len(contracts)}\n\n"
    for c in contracts[:5]:
        context += f"Contract: {c.title} ({c.contract_type}) with {c.counterparty_name}\n"
        res_clauses = await session.execute(
            select(ContractClause).where(ContractClause.contract_id == c.id).limit(3)
        )
        for cl in res_clauses.scalars().all():
            context += f"  [{cl.clause_type}] {cl.clause_text[:300]}\n"
        context += "\n"

    try:
        answer = await chat_answer(question, context)
    except GeminiUnavailableError:
        # Graceful fallback for portfolio chat
        answer = f"🤖 REXI Fallback (LLM unavailable)\n\nBased on your question about '{question}', here are relevant excerpts from {len(contracts)} contracts:\n\n{context[:3000]}"
    return {"org_id": org_id, "question": question, "answer": answer, "contracts_searched": len(contracts)}
