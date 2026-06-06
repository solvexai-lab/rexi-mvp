"""PII detection tests for Indian identifiers + Presidio enhancement.

NOTE: Presidio engines are mocked to avoid loading heavy spaCy models
(>100MB RAM) in the CI/test environment. Custom Indian regex patterns
are tested directly.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.services.pii_service import PIIAnalyzer, pii_analyzer
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_pii_analyzer():
    """Reset analyzer state between tests to avoid Presidio init bleed.
    
    Sets _presidio_available=False (not None) so regular tests skip
    Presidio loading. Mock-based Presidio tests explicitly re-enable it.
    """
    pii_analyzer._presidio_available = False
    pii_analyzer._analyzer = None
    pii_analyzer._anonymizer = None
    yield
    pii_analyzer._presidio_available = False
    pii_analyzer._analyzer = None
    pii_analyzer._anonymizer = None


class _MockPresidioResult:
    """Lightweight stand-in for Presidio RecognizerResult."""
    def __init__(self, entity_type, start, end, score):
        self.entity_type = entity_type
        self.start = start
        self.end = end
        self.score = score

def _mock_presidio_findings(entity_type, start, end, score, text):
    """Helper to create mock Presidio result objects."""
    return _MockPresidioResult(entity_type, start, end, score)


# ── Core Indian Pattern Tests ──

@pytest.mark.asyncio
async def test_detect_aadhaar():
    text = "My Aadhaar is 1234 5678 9012 and my PAN is ABCDE1234F."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "AADHAAR" in types
    assert "PAN" in types


@pytest.mark.asyncio
async def test_detect_gstin():
    text = "GSTIN: 27AABCU9603R1ZX for vendor billing."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "GSTIN" in types


@pytest.mark.asyncio
async def test_detect_phone_and_email():
    text = "Contact me at test@email.com or call +91-9876543210."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "EMAIL" in types
    assert "INDIAN_PHONE" in types


@pytest.mark.asyncio
async def test_detect_upi_and_ifsc():
    text = "Send payment to user@upi or use IFSC HDFC0123456."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "UPI" in types
    assert "IFSC" in types


@pytest.mark.asyncio
async def test_detect_passport():
    text = "My passport number is A12345678 for international travel."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "PASSPORT" in types


@pytest.mark.asyncio
async def test_anonymize():
    text = "Contact me at test@email.com or call +91-9876543210."
    result = pii_analyzer.anonymize(text)
    assert result["has_pii"] is True
    assert "test@email.com" not in result["anonymized"]
    assert "9876543210" not in result["anonymized"]


@pytest.mark.asyncio
async def test_anonymize_aadhaar():
    text = "My Aadhaar is 123456789012."
    result = pii_analyzer.anonymize(text)
    assert result["has_pii"] is True
    assert "XXXX XXXX 9012" in result["anonymized"]


@pytest.mark.asyncio
async def test_anonymize_pan():
    text = "My PAN is ABCDE1234F."
    result = pii_analyzer.anonymize(text)
    assert result["has_pii"] is True
    assert "AB*****F" in result["anonymized"]


@pytest.mark.asyncio
async def test_validate_pan():
    result = pii_analyzer.validate_indian_id("PAN", "ABCDE1234F")
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_invalid_pan():
    result = pii_analyzer.validate_indian_id("PAN", "INVALID")
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_validate_gstin():
    result = pii_analyzer.validate_indian_id("GSTIN", "27AABCU9603R1ZX")
    assert result["valid"] is True
    assert "State code: 27" in result["detail"]


@pytest.mark.asyncio
async def test_validate_aadhaar():
    result = pii_analyzer.validate_indian_id("AADHAAR", "123456789012")
    assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_ifsc():
    result = pii_analyzer.validate_indian_id("IFSC", "HDFC0123456")
    assert result["valid"] is True
    assert "Bank: HDFC" in result["detail"]


# ── Presidio Enhancement Tests (with mocks) ──

@pytest.mark.asyncio
async def test_presidio_detects_credit_card():
    """Test that Presidio findings are merged with custom patterns."""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = [
        _mock_presidio_findings("CREDIT_CARD", 18, 34, 0.95, "4111111111111112")
    ]
    pii_analyzer._analyzer = mock_analyzer
    pii_analyzer._presidio_available = True

    text = "My credit card is 4111111111111112."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "CREDIT_CARD" in types


@pytest.mark.asyncio
async def test_presidio_deduplication_with_custom():
    """When Presidio returns same span as custom regex, only one is kept."""
    mock_analyzer = MagicMock()
    # Presidio returns EMAIL at exact same position as regex
    mock_analyzer.analyze.return_value = [
        _mock_presidio_findings("EMAIL", 13, 27, 0.95, "user@test.com")
    ]
    pii_analyzer._analyzer = mock_analyzer
    pii_analyzer._presidio_available = True

    text = "Email me at user@test.com today."
    findings = pii_analyzer.analyze(text)
    email_findings = [f for f in findings if f["entity_type"] in ("EMAIL", "EMAIL")]
    # Deduplication by exact span keeps only one
    assert len(email_findings) == 1


@pytest.mark.asyncio
async def test_presidio_graceful_failure():
    """If Presidio analyze() raises, custom patterns still work."""
    mock_analyzer = MagicMock()
    mock_analyzer.analyze.side_effect = RuntimeError("model error")
    pii_analyzer._analyzer = mock_analyzer
    pii_analyzer._presidio_available = True

    text = "My PAN is ABCDE1234F."
    findings = pii_analyzer.analyze(text)
    types = [f["entity_type"] for f in findings]
    assert "PAN" in types


@pytest.mark.asyncio
async def test_deduplication():
    text = "ABCDE1234F ABCDE1234F"
    findings = pii_analyzer.analyze(text)
    pan_findings = [f for f in findings if f["entity_type"] == "PAN"]
    # Two PANs at different positions are distinct non-overlapping spans
    assert len(pan_findings) == 2
    assert pan_findings[0]["start"] != pan_findings[1]["start"]


@pytest.mark.asyncio
async def test_overlap_deduplication():
    # A 12-digit number could match both AADHAAR and BANK_ACCOUNT
    # The higher-scoring one should win
    text = "My ID is 123456789012."
    findings = pii_analyzer.analyze(text)
    spans = [(f["start"], f["end"]) for f in findings]
    unique_spans = set(spans)
    # All returned spans should be unique (no overlaps)
    assert len(spans) == len(unique_spans)


@pytest.mark.asyncio
async def test_no_pii_returns_empty():
    text = "This is a clean sentence with no identifiers."
    findings = pii_analyzer.analyze(text)
    assert len(findings) == 0
    result = pii_analyzer.anonymize(text)
    assert result["has_pii"] is False
    assert result["anonymized"] == text


# ── API Endpoint Tests ──

def test_api_analyze():
    response = client.post("/api/v1/pii/analyze", json={"text": "My PAN is ABCDE1234F."})
    assert response.status_code == 200
    data = response.json()
    assert data["has_pii"] is True
    assert "PAN" in data["entity_types"]


def test_api_analyze_no_pii():
    response = client.post("/api/v1/pii/analyze", json={"text": "Hello world."})
    assert response.status_code == 200
    data = response.json()
    assert data["has_pii"] is False
    assert data["findings"] == []


def test_api_analyze_empty_text():
    response = client.post("/api/v1/pii/analyze", json={"text": ""})
    assert response.status_code == 400


def test_api_anonymize():
    response = client.post("/api/v1/pii/anonymize", json={"text": "Email me at user@test.com", "mask_char": "#"})
    assert response.status_code == 200
    data = response.json()
    assert data["has_pii"] is True
    assert "user@test.com" not in data["anonymized"]


def test_api_validate_pan():
    response = client.post("/api/v1/pii/validate", json={"id_type": "PAN", "value": "ABCDE1234F"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True


def test_api_validate_invalid_type():
    response = client.post("/api/v1/pii/validate", json={"id_type": "SSN", "value": "123-45-6789"})
    assert response.status_code == 400


def test_api_status():
    response = client.get("/api/v1/pii/status")
    assert response.status_code == 200
    data = response.json()
    assert "presidio_installed" in data
    assert "presidio_initialized" in data
    assert "indian_patterns" in data
    assert len(data["indian_patterns"]) > 0


# ── Service Status Tests ──

def test_pii_analyzer_singleton():
    assert pii_analyzer is not None
    assert isinstance(pii_analyzer, PIIAnalyzer)


def test_presidio_lazy_initialization():
    """Presidio should NOT be initialized at module import time."""
    fresh = PIIAnalyzer()
    assert fresh._presidio_available is None
    assert fresh._analyzer is None
    assert fresh._anonymizer is None


def test_presidio_availability_with_mock():
    """Availability flag works when Presidio is mocked."""
    fresh = PIIAnalyzer()
    fresh._analyzer = MagicMock()
    fresh._anonymizer = MagicMock()
    fresh._presidio_available = True
    assert fresh.presidio_available is True
    assert fresh.analyzer is not None
    assert fresh.anonymizer is not None
