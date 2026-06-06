"""LLM prompts for contract analysis.

Uses contractguard.prompts directly from vendor/contractguard
with REXI_CONTEXT prefix for Indian commercial contract context.
"""

from contractguard.prompts import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_ZH,
    ANALYSIS_PROMPT,
    ANALYSIS_PROMPT_ZH,
    get_prompts as _cg_get_prompts,
)

REXI_CONTEXT = """You are analyzing Indian commercial contracts for a company using the REXI platform.
Consider Indian law context: Indian Contract Act 1872, DPDP Act 2023, SEBI LODR, Companies Act 2013.
Analyze from the COMPANY's perspective (not the counterparty)."""


__all__ = [
    "REXI_CONTEXT",
    "SYSTEM_PROMPT",
    "SYSTEM_PROMPT_ZH",
    "ANALYSIS_PROMPT",
    "ANALYSIS_PROMPT_ZH",
    "get_prompts",
]


def get_prompts(lang: str = "en") -> tuple[str, str]:
    """Return (system_prompt, analysis_prompt) for the given language."""
    return _cg_get_prompts(lang)
