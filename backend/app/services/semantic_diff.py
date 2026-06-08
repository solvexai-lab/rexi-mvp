"""Semantic clause-level diff.
COPIED VERBATIM from: vendor/multi-agent-contract/apps/api/cip/agents/clause_compare.py
ADAPTATIONS:
- Removed `from cip.compare.semantic import nli_infer` (their internal module)
- Replaced `nli_infer()` with our `_semantic_similarity()` + label mapping
- Kept `_numbers()`, `_diff_bullets()`, `ClauseCompareResult`, `ClauseComparisonAgent` EXACT
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
import difflib
import re

# Our local semantic similarity (replaces their nli_infer)
# Lazy-load the model to avoid 400MB+ RAM usage at import time.
_ST_AVAILABLE = None
_st_model = None

def _ensure_st_model():
    global _ST_AVAILABLE, _st_model
    if _ST_AVAILABLE is not None:
        return _ST_AVAILABLE
    try:
        from sentence_transformers import SentenceTransformer, util
        _st_model = SentenceTransformer('all-MiniLM-L6-v2')
        _ST_AVAILABLE = True
    except Exception:
        _ST_AVAILABLE = False
        _st_model = None
    return _ST_AVAILABLE


@dataclass
class ClauseCompareResult:
    """Clause-level comparison result.
    - NLI-first semantic label (entails/contradicts/neutral) with confidence
    - Deterministic, auditable key differences (no LLM required)
    - Optional LLM can be layered for narrative, but core judgment is model+rules
    """
    label: str
    change_summary: str
    key_differences: list[str]
    risk_note: str
    prompt_version: str
    llm_metrics: dict | None


def _numbers(s: str) -> list[str]:
    return re.findall(r"\b\d+(?:\.\d+)?\b", (s or "").replace(",", ""))

def _diff_bullets(a: str, b: str, *, max_bullets: int = 6) -> list[str]:
    a = (a or "").strip()
    b = (b or "").strip()
    if not a and not b:
        return []
    bullets: List[str] = []

    na = _numbers(a)
    nb = _numbers(b)
    if na != nb and (na or nb):
        bullets.append(f"Numeric terms changed: {na[:5]} → {nb[:5]}")
    # negation / carve-outs
    for kw in ["not", "no", "without", "except", "unless", "subject to"]:
        if (kw in a.lower()) != (kw in b.lower()):
            bullets.append(f"Carve-out/negation changed: '{kw}' presence differs")

    # text deltas
    sm = difflib.SequenceMatcher(a=a, b=b)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        seg_a = a[i1:i2].strip()
        seg_b = b[j1:j2].strip()
        if tag == "replace":
            bullets.append(f"Replaced: '{seg_a[:80]}' → '{seg_b[:80]}'")
        elif tag == "delete":
            bullets.append(f"Removed: '{seg_a[:120]}'")
        elif tag == "insert":
            bullets.append(f"Added: '{seg_b[:120]}'")
        if len(bullets) >= max_bullets:
            break

    return bullets[:max_bullets]


# ── Adapter: their nli_infer → our semantic similarity ──
class _NLIResult:
    def __init__(self, label: str, confidence: float, method: str, model: str, cache_hit: bool):
        self.label = label
        self.confidence = confidence
        self.method = method
        self.model = model
        self.cache_hit = cache_hit


def _semantic_similarity(a: str, b: str) -> float:
    if _ensure_st_model() and _st_model is not None:
        try:
            from sentence_transformers import util
            emb1 = _st_model.encode(a, convert_to_tensor=True)
            emb2 = _st_model.encode(b, convert_to_tensor=True)
            return float(util.cos_sim(emb1, emb2)[0][0])
        except Exception:
            pass
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _nli_infer(left: str, right: str) -> _NLIResult:
    """Replacement for their nli_infer(). Maps cosine similarity to entailment labels."""
    sim = _semantic_similarity(left, right)
    if sim > 0.90:
        label = "entails"
    elif sim < 0.40:
        label = "contradicts"
    else:
        label = "neutral"
    return _NLIResult(
        label=label,
        confidence=round(sim, 3),
        method="cosine_similarity",
        model="all-MiniLM-L6-v2" if _ST_AVAILABLE else "jaccard_fallback",
        cache_hit=False,
    )


class ClauseComparisonAgent:
    """Enterprise clause comparison agent.

    This agent intentionally avoids relying on external LLMs to make semantic judgments.
    It uses a local NLI model (CrossEncoder) when available, and a deterministic baseline otherwise.
    """
    name = "clause_compare"

    def __init__(self, *, version: str = "v1") -> None:
        self.version = version

    async def run(self, left: str | None, right: str | None) -> ClauseCompareResult:
        left = left or ""
        right = right or ""

        res = _nli_infer(left, right)

        # change summary
        if not left.strip() and right.strip():
            change_summary = "Clause added in the new version."
        elif left.strip() and not right.strip():
            change_summary = "Clause removed in the new version."
        elif res.label == "entails":
            change_summary = "No material semantic change detected (new text entails the prior obligations)." if left.strip() else "No material semantic change detected."
        elif res.label == "contradicts":
            change_summary = "Material semantic change detected (contradiction / obligation shift)."
        else:
            change_summary = "Potential semantic drift detected; requires legal review."

        diffs = _diff_bullets(left, right)

        # risk note is intentionally conservative here; deeper risk scoring happens in Risk Agent.
        risk_note = ""
        if res.label == "contradicts":
            risk_note = "High attention: contradiction detected; review for liability, termination, payment or remedy shifts."
        elif (not left.strip()) != (not right.strip()):
            risk_note = "Review added/removed clause for alignment with playbook and required protections."
        else:
            risk_note = ""

        return ClauseCompareResult(
            label=res.label,
            change_summary=change_summary,
            key_differences=diffs,
            risk_note=risk_note,
            prompt_version=self.version,
            llm_metrics={"nli": {"confidence": res.confidence, "method": res.method, "model": res.model, "cache_hit": res.cache_hit}},
        )


# ── Legacy compatibility with Day 1 code ──
@dataclass
class SemanticCompareResult:
    label: str
    change_summary: str
    key_differences: List[str]
    similarity_score: float
    risk_delta: str
    old_text: str
    new_text: str


async def compare_clauses(old_text: str | None, new_text: str | None) -> SemanticCompareResult:
    agent = ClauseComparisonAgent()
    result = await agent.run(old_text, new_text)

    # Map their label to our label space
    label_map = {
        "entails": "semantically_equivalent",
        "contradicts": "material_change",
        "neutral": "modified",
    }
    label = label_map.get(result.label, result.label)

    if not old_text and new_text:
        label = "added"
    elif old_text and not new_text:
        label = "removed"

    sim = result.llm_metrics.get("nli", {}).get("confidence", 0.5)
    if label == "added" or label == "removed":
        risk = "±unknown"
    elif label == "unchanged" or label == "semantically_equivalent":
        risk = "±0%"
    elif label == "modified":
        risk = "±10-20%"
    else:
        risk = "+20-50%"

    return SemanticCompareResult(
        label=label,
        change_summary=result.change_summary,
        key_differences=result.key_differences,
        similarity_score=round(sim, 3),
        risk_delta=risk,
        old_text=old_text or "",
        new_text=new_text or "",
    )


async def compare_contracts(clauses_a: List[dict], clauses_b: List[dict]) -> List[SemanticCompareResult]:
    map_a = {c["clause_type"]: c.get("clause_text", "") for c in clauses_a}
    map_b = {c["clause_type"]: c.get("clause_text", "") for c in clauses_b}
    all_types = set(map_a.keys()) | set(map_b.keys())
    return [await compare_clauses(map_a.get(ct), map_b.get(ct)) for ct in sorted(all_types)]
