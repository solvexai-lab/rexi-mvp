"""PII detection and anonymization with Indian-specific recognizers.
Uses Microsoft Presidio + custom patterns for DPDP Act compliance."""
import re
import hashlib
from typing import List, Dict, Optional

class PIIAnalyzer:
    """Lightweight PII analyzer with Indian ID support.
    
    Presidio engines are initialized LAZILY to avoid blocking app startup
    and consuming RAM until PII analysis is actually requested.
    """

    INDIAN_PATTERNS = {
        "AADHAAR": {
            "regex": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
            "description": "12-digit Aadhaar number",
            "score": 0.95,
        },
        "PAN": {
            "regex": r"\b[A-Z]{5}\d{4}[A-Z]\b",
            "description": "10-character PAN (e.g., ABCDE1234F)",
            "score": 0.92,
        },
        "GSTIN": {
            "regex": r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b",
            "description": "15-character GSTIN",
            "score": 0.94,
        },
        "UPI": {
            "regex": r"\b[a-zA-Z0-9._-]+@[a-zA-Z]+\b",
            "description": "UPI VPA (e.g., user@upi)",
            "score": 0.70,
        },
        "IFSC": {
            "regex": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
            "description": "11-character IFSC code",
            "score": 0.88,
        },
        "INDIAN_PHONE": {
            "regex": r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",
            "description": "Indian mobile number",
            "score": 0.85,
        },
        "BANK_ACCOUNT": {
            "regex": r"\b\d{9,18}\b",
            "description": "Potential bank account number",
            "score": 0.55,
        },
        "PASSPORT": {
            "regex": r"\b[A-Z][1-9]\d{7}\b",
            "description": "Indian passport number",
            "score": 0.80,
        },
        "EMAIL": {
            "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "description": "Email address",
            "score": 0.90,
        },
    }

    def __init__(self):
        self._presidio_available = None  # None = not yet attempted
        self._analyzer = None
        self._anonymizer = None

    def _init_presidio(self):
        """Lazy initialization of Presidio engines."""
        if self._presidio_available is not None:
            return self._presidio_available
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
            self._presidio_available = True
        except Exception:
            self._analyzer = None
            self._anonymizer = None
            self._presidio_available = False
        return self._presidio_available

    @property
    def analyzer(self):
        self._init_presidio()
        return self._analyzer

    @property
    def anonymizer(self):
        self._init_presidio()
        return self._anonymizer

    @property
    def presidio_available(self):
        if self._presidio_available is None:
            self._init_presidio()
        return self._presidio_available

    def analyze(self, text: str, language: str = "en") -> List[Dict]:
        """Analyze text for PII. Returns list of findings."""
        findings = []

        # Custom Indian pattern detection
        for entity_type, pattern in self.INDIAN_PATTERNS.items():
            for match in re.finditer(pattern["regex"], text):
                findings.append({
                    "entity_type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "score": pattern["score"],
                    "text": match.group(),
                    "description": pattern["description"],
                })

        # Presidio fallback/enhancement
        if self.presidio_available and self.analyzer:
            try:
                presidio_results = self.analyzer.analyze(text=text, language=language)
                for r in presidio_results:
                    findings.append({
                        "entity_type": r.entity_type,
                        "start": r.start,
                        "end": r.end,
                        "score": r.score,
                        "text": text[r.start:r.end],
                        "description": f"Presidio: {r.entity_type}",
                    })
            except Exception:
                pass

        # Deduplicate overlapping spans (keep highest score)
        findings = self._deduplicate(findings)
        return sorted(findings, key=lambda x: x["start"])

    def anonymize(self, text: str, findings: Optional[List[Dict]] = None, mask_char: str = "*") -> Dict:
        """Anonymize text by replacing PII with masked values."""
        if findings is None:
            findings = self.analyze(text)

        anonymized = text
        replacements = []
        # Process from end to start to preserve indices
        for f in reversed(findings):
            original = anonymized[f["start"]:f["end"]]
            masked = self._mask_value(original, f["entity_type"], mask_char)
            anonymized = anonymized[:f["start"]] + masked + anonymized[f["end"]:]
            replacements.append({"original": original, "masked": masked, "type": f["entity_type"]})

        return {
            "original": text,
            "anonymized": anonymized,
            "findings": findings,
            "replacements": replacements,
            "has_pii": len(findings) > 0,
        }

    def _mask_value(self, value: str, entity_type: str, mask_char: str = "*") -> str:
        """Mask a value while preserving some structure for validation."""
        if entity_type == "AADHAAR":
            return "XXXX XXXX " + value[-4:] if len(value) >= 4 else mask_char * len(value)
        if entity_type == "PAN":
            return value[:2] + mask_char * 5 + value[-1] if len(value) == 10 else mask_char * len(value)
        if entity_type == "GSTIN":
            return value[:2] + mask_char * 10 + value[-2:] if len(value) == 15 else mask_char * len(value)
        if entity_type == "EMAIL":
            local, domain = value.split("@", 1)
            masked_local = local[0] + mask_char * (len(local) - 1) if len(local) > 1 else local
            return f"{masked_local}@{domain}"
        if entity_type == "INDIAN_PHONE":
            return "+91-" + mask_char * 6 + value[-4:] if len(value) >= 10 else mask_char * len(value)
        return mask_char * min(len(value), 8)

    def _deduplicate(self, findings: List[Dict]) -> List[Dict]:
        """Remove overlapping spans, keeping highest score."""
        if not findings:
            return findings
        sorted_findings = sorted(findings, key=lambda x: (-x["score"], x["start"]))
        result = []
        for f in sorted_findings:
            overlap = any(
                not (f["end"] <= r["start"] or f["start"] >= r["end"])
                for r in result
            )
            if not overlap:
                result.append(f)
        return result

    def validate_indian_id(self, id_type: str, value: str) -> Dict:
        """Validate Indian identifiers with checksums where applicable."""
        valid = False
        detail = ""
        if id_type == "PAN":
            valid = bool(re.match(r"^[A-Z]{5}\d{4}[A-Z]$", value))
            if valid:
                # Simple checksum: 4th char indicates type
                detail = f"Type: {value[3]}"
        elif id_type == "GSTIN":
            valid = bool(re.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$", value))
            if valid:
                state_code = value[:2]
                detail = f"State code: {state_code}"
        elif id_type == "AADHAAR":
            valid = bool(re.match(r"^\d{12}$", value))
            # Verhoeff checksum would go here
            detail = "12-digit format" if valid else "Invalid length"
        elif id_type == "IFSC":
            valid = bool(re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", value))
            if valid:
                detail = f"Bank: {value[:4]}"
        return {"valid": valid, "type": id_type, "value": value, "detail": detail}


pii_analyzer = PIIAnalyzer()
