"""Gemini LLM service adapted from ClauseIQ + ContractGuard patterns.
Handles plain English translation, risk analysis, and chat.
"""
import os
import json
import re
import httpx
from typing import List, Dict, Any, Optional

# Import verbatim prompts from ContractGuard
from app.services.prompts import SYSTEM_PROMPT as REXI_SYSTEM_PROMPT, ANALYSIS_PROMPT as REXI_ANALYSIS_PROMPT

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# ── Prompts copied & adapted from ContractGuard + ClauseIQ ──

PLAIN_ENGLISH_SYSTEM = """You are a legal translator specializing in Indian commercial contracts.
Convert complex legal clauses into plain English that a non-lawyer CEO can understand.
Be precise about obligations, dates, penalties, and rights.
Use simple words. Keep all financial and legal consequences explicit."""

PLAIN_ENGLISH_PROMPT = """Analyze this contract clause and provide:
1. A plain English translation (what it actually means in simple terms)
2. Risk level (High/Medium/Low) with explanation
3. Suggestions for improvement or negotiation

Clause type: {clause_type}
Clause text:
---
{clause_text}
---

Respond ONLY with valid JSON in this exact format:
{{
    "plain_english": "Simple explanation...",
    "risk_level": "High|Medium|Low",
    "risk_explanation": "Why this is risky...",
    "suggestions": "What to negotiate..."
}}"""

# Use ContractGuard's ANALYSIS_PROMPT verbatim (imported above as REXI_ANALYSIS_PROMPT)
RISK_ANALYSIS_PROMPT = REXI_ANALYSIS_PROMPT

WHAT_IF_PROMPT = """Compare ORIGINAL vs PROPOSED clause against COMPANY PLAYBOOK STANDARD.

ORIGINAL:
{original_clause}

PROPOSED:
{proposed_clause}

PLAYBOOK STANDARD:
{playbook_standard}

Analyze and return JSON:
{{
    "risk_delta": "+15% (higher risk) or -10% (lower risk)",
    "playbook_deviation": "GREEN|YELLOW|RED",
    "financial_impact": "e.g., ₹250K additional exposure",
    "negotiation_leverage": "stronger|weaker|neutral",
    "recommendation": "Accept|Counter-propose|Reject",
    "reasoning": "Detailed explanation..."
}}"""

CHAT_PROMPT = """You are REXI, an AI legal assistant for Indian contract review.
Answer the user's question based ONLY on the provided contract context.
If the answer is not in the context, say so clearly.
Do not make up information.

Contract Context:
{context}

User Question: {question}

Provide a clear, concise answer with citations to specific clauses where relevant."""


def _clean_json_response(text: str) -> str:
    """Clean markdown code blocks from LLM response. Copied from ClauseIQ."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    # Try to find JSON object/array
    obj_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if obj_match:
        return obj_match.group(0)
    arr_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if arr_match:
        return arr_match.group(0)
    return cleaned.strip()


class GeminiUnavailableError(Exception):
    """Raised when Gemini API key is missing or the API is unreachable."""
    pass


async def _gemini_generate(prompt: str, temperature: float = 0.1) -> str:
    """Generate text using Gemini API via HTTP."""
    if not GEMINI_API_KEY:
        raise GeminiUnavailableError("GEMINI_API_KEY not configured")

    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                url,
                params={"key": GEMINI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": 4096}
                },
                timeout=60
            )
            r.raise_for_status()
            data = r.json()
            # Guard against safety-blocked or malformed responses
            candidates = data.get("candidates", [])
            if not candidates:
                raise GeminiUnavailableError("Gemini returned no candidates (possibly safety-blocked)")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise GeminiUnavailableError("Gemini response missing content parts")
            return parts[0].get("text", "")
        except httpx.HTTPStatusError as e:
            raise GeminiUnavailableError(f"Gemini API error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise GeminiUnavailableError(f"Gemini API unreachable: {str(e)}")


async def translate_clause_to_plain_english(clause_type: str, clause_text: str) -> Dict[str, str]:
    """Adapted from ClauseIQ's analyze_legal_document()."""
    prompt = PLAIN_ENGLISH_PROMPT.format(clause_type=clause_type, clause_text=clause_text[:4000])
    raw = await _gemini_generate(prompt, temperature=0.2)
    cleaned = _clean_json_response(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "plain_english": "Could not parse AI response. Raw: " + raw[:200],
            "risk_level": "medium",
            "risk_explanation": "Parsing error",
            "suggestions": "Retry analysis"
        }


async def analyze_clause_risk(clause_text: str) -> Dict[str, Any]:
    """Adapted from ContractGuard's analyze_contract()."""
    prompt = RISK_ANALYSIS_PROMPT.format(clause_text=clause_text[:6000])
    raw = await _gemini_generate(prompt, temperature=0.1)
    cleaned = _clean_json_response(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "contract_type": "unknown",
            "summary": "Analysis failed",
            "red_flags": [],
            "warnings": [],
            "good_clauses": [],
            "missing_protections": [],
            "fairness_score": 50,
            "fairness_grade": "C"
        }


async def what_if_simulate(original_clause: str, proposed_clause: str, playbook_standard: str) -> Dict[str, str]:
    """What-if scenario simulation."""
    prompt = WHAT_IF_PROMPT.format(
        original_clause=original_clause[:2000],
        proposed_clause=proposed_clause[:2000],
        playbook_standard=playbook_standard[:2000]
    )
    raw = await _gemini_generate(prompt, temperature=0.2)
    cleaned = _clean_json_response(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "risk_delta": "unknown",
            "playbook_deviation": "YELLOW",
            "financial_impact": "Unable to calculate",
            "negotiation_leverage": "neutral",
            "recommendation": "Review manually",
            "reasoning": raw[:500]
        }


async def chat_answer(question: str, context: str) -> str:
    """RAG chat answer. Adapted from ClauseIQ's answer_legal_question()."""
    prompt = CHAT_PROMPT.format(context=context[:6000], question=question)
    return await _gemini_generate(prompt, temperature=0.3)


async def stream_chat_answer(question: str, context: str):
    """Streaming chat for SSE. Yields token chunks."""
    if not GEMINI_API_KEY:
        raise GeminiUnavailableError("GEMINI_API_KEY not configured")

    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:streamGenerateContent"
    prompt = CHAT_PROMPT.format(context=context[:6000], question=question)
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            url,
            params={"key": GEMINI_API_KEY, "alt": "sse"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096}
            },
            timeout=120
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield text
                    except Exception:
                        pass
