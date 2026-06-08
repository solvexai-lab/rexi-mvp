"""Contract playbook evaluation — heuristic rule checking against extracted clauses.

Evaluates a contract's clauses against the organization's playbook rules.
Uses keyword matching and number extraction for must_have / min_value / max_value conditions.
Designed for deterministic, explainable results suitable for legal demos.
"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


SEVERITY_WEIGHTS = {"critical": 15, "high": 10, "medium": 5, "low": 2}


def _extract_numbers(text: str) -> List[int]:
    """Extract all integers from text, filtering out years. Handles written numbers loosely."""
    if not text:
        return []
    # Direct digits — filter out years (1900-2100) as they're usually dates, not contract terms
    nums = [int(n) for n in re.findall(r'\b(\d+)\b', text) if not (1900 <= int(n) <= 2100)]
    # Written numbers (basic)
    written_map = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "thirty": 30, "sixty": 60, "ninety": 90, "hundred": 100,
    }
    lower = text.lower()
    for word, val in written_map.items():
        if word in lower and val not in nums:
            nums.append(val)
    return nums


def _keyword_matches(condition_value: str, text: str) -> bool:
    """Check if clause text satisfies a must_have keyword condition."""
    t = text.lower()
    mapping: Dict[str, List[str]] = {
        "india": ["india", "indian", "bharat", "republic of india"],
        "mutual": ["mutual", "each party", "both parties", "reciprocal", "bilateral"],
        "explicit_clause": ["renew", "auto-renew", "automatic renewal", "extension"],
        "explicit_list": ["•", "- ", "(a)", "(b)", "(i)", "(ii)", "1.", "2.", "following:", "include:"],
        "insurance": ["insurance", "policy", "coverage", "insured"],
        "sla": ["sla", "service level", "uptime", "availability", "response time"],
        "gratuity": ["gratuity", "payment of gratuity", "gratuity act"],
        "background_check": ["background", "verification", "police verification", "reference check"],
        "india_storage": ["india", "within india", "local storage", "data localisation", "in-country"],
        "uat": ["uat", "user acceptance", "acceptance testing", "acceptance criteria"],
        "exit_clause": ["exit", "data export", "portability", "migration", "handover"],
        "yes": [],  # Generic — any clause of this type satisfies
        "explicit": [],  # Generic — any clause of this type satisfies
    }
    keywords = mapping.get(condition_value, [condition_value])
    if not keywords:
        # Generic yes/explicit — just having the clause is enough
        return True
    return any(kw in t for kw in keywords)


def _check_value_condition(condition: str, threshold_str: str, clause_text: str) -> tuple[bool, Optional[int]]:
    """Check min_value / max_value condition against clause text.
    Returns (passes, extracted_value_or_none).
    """
    numbers = _extract_numbers(clause_text)
    if not numbers:
        return False, None

    try:
        threshold = int(threshold_str)
    except ValueError:
        return False, None

    # For both min_value and max_value, the relevant contract term is typically
    # the largest non-year number in the clause text (e.g., "thirty (30) days"
    # among "three (3) years"). We use max after filtering years.
    extracted = max(numbers)
    if condition == "min_value":
        passes = extracted >= threshold
    else:  # max_value
        passes = extracted <= threshold

    return passes, extracted


@dataclass
class PlaybookViolation:
    rule_name: str
    rule_type: str
    severity: str
    condition: str
    expected: str
    found: str
    clause_text_snippet: str = ""


def evaluate_contract(
    contract_type: str,
    clauses: List[Dict[str, Any]],
    rules: List[Any],
) -> Dict[str, Any]:
    """Evaluate a contract against playbook rules.

    Args:
        contract_type: e.g. 'nda', 'vendor', 'employment', 'license'
        clauses: List of dicts with 'clause_type', 'clause_text', 'id'
        rules: List of PlaybookRule SQLModel objects

    Returns:
        {
            "score": int (0-100),
            "max_score": 100,
            "violations": [...],
            "passed": int,
            "total_checked": int,
            "severity_breakdown": {"critical": N, "high": N, ...}
        }
    """
    violations: List[Dict[str, Any]] = []
    passed = 0
    severity_breakdown: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    # Filter rules applicable to this contract type
    applicable = [
        r for r in rules
        if r.is_active and (not r.contract_type or r.contract_type.lower() == contract_type.lower())
    ]

    for rule in applicable:
        # Find clauses matching this rule's type
        matching = [c for c in clauses if c.get("clause_type", "").lower() == rule.rule_type.lower()]
        combined_text = " ".join(c.get("clause_text", "") for c in matching)

        if rule.condition == "must_have":
            if not matching or not _keyword_matches(rule.threshold_value, combined_text):
                violations.append({
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "severity": rule.severity,
                    "condition": rule.condition,
                    "expected": rule.threshold_value,
                    "found": "missing or insufficient",
                    "clause_text_snippet": combined_text[:200] if combined_text else "",
                })
                severity_breakdown[rule.severity] = severity_breakdown.get(rule.severity, 0) + 1
            else:
                passed += 1

        elif rule.condition in ("min_value", "max_value"):
            if not matching:
                violations.append({
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "severity": rule.severity,
                    "condition": rule.condition,
                    "expected": f"{rule.condition.replace('_', ' ')} {rule.threshold_value}",
                    "found": "clause missing",
                    "clause_text_snippet": "",
                })
                severity_breakdown[rule.severity] = severity_breakdown.get(rule.severity, 0) + 1
            else:
                passes, extracted = _check_value_condition(rule.condition, rule.threshold_value, combined_text)
                if passes:
                    passed += 1
                else:
                    found_str = f"{extracted}" if extracted is not None else "no numeric value found"
                    violations.append({
                        "rule_name": rule.rule_name,
                        "rule_type": rule.rule_type,
                        "severity": rule.severity,
                        "condition": rule.condition,
                        "expected": f"{rule.condition.replace('_', ' ')} {rule.threshold_value}",
                        "found": found_str,
                        "clause_text_snippet": combined_text[:200],
                    })
                    severity_breakdown[rule.severity] = severity_breakdown.get(rule.severity, 0) + 1

    # Score calculation
    penalty = sum(SEVERITY_WEIGHTS.get(v["severity"], 5) for v in violations)
    score = max(0, 100 - penalty)

    return {
        "score": score,
        "max_score": 100,
        "violations": violations,
        "passed": passed,
        "total_checked": len(applicable),
        "severity_breakdown": severity_breakdown,
    }
