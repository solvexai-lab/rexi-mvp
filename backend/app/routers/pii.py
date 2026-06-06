"""PII detection and anonymization API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.services.pii_service import pii_analyzer

router = APIRouter(prefix="/api/v1/pii", tags=["pii"])


class AnalyzeRequest(BaseModel):
    text: str
    language: str = "en"


class AnalyzeResponse(BaseModel):
    findings: List[dict]
    has_pii: bool
    entity_types: List[str]


class AnonymizeRequest(BaseModel):
    text: str
    mask_char: str = "*"


class AnonymizeResponse(BaseModel):
    original: str
    anonymized: str
    has_pii: bool
    findings: List[dict]
    replacements: List[dict]


class ValidateRequest(BaseModel):
    id_type: str
    value: str


class ValidateResponse(BaseModel):
    valid: bool
    type: str
    value: str
    detail: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(req: AnalyzeRequest):
    """Analyze text for PII entities (Indian IDs + Presidio entities)."""
    if not req.text or len(req.text) > 500_000:
        raise HTTPException(status_code=400, detail="Text must be between 1 and 500,000 characters")
    findings = pii_analyzer.analyze(req.text, language=req.language)
    return AnalyzeResponse(
        findings=findings,
        has_pii=len(findings) > 0,
        entity_types=list(dict.fromkeys(f["entity_type"] for f in findings)),
    )


@router.post("/anonymize", response_model=AnonymizeResponse)
async def anonymize_text(req: AnonymizeRequest):
    """Anonymize text by masking detected PII."""
    if not req.text or len(req.text) > 500_000:
        raise HTTPException(status_code=400, detail="Text must be between 1 and 500,000 characters")
    result = pii_analyzer.anonymize(req.text, mask_char=req.mask_char)
    return AnonymizeResponse(**result)


@router.post("/validate", response_model=ValidateResponse)
async def validate_id(req: ValidateRequest):
    """Validate an Indian identifier (PAN, GSTIN, AADHAAR, IFSC)."""
    if req.id_type.upper() not in ("PAN", "GSTIN", "AADHAAR", "IFSC"):
        raise HTTPException(status_code=400, detail="Supported types: PAN, GSTIN, AADHAAR, IFSC")
    result = pii_analyzer.validate_indian_id(req.id_type.upper(), req.value)
    return ValidateResponse(**result)


@router.post("/contracts/{contract_id}/scan")
async def scan_contract_pii(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Scan a contract's parsed text for PII entities."""
    from app.models.tables import Contract
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not contract.parsed_text:
        return {"contract_id": contract_id, "findings": [], "has_pii": False, "anonymized_preview": ""}

    findings = pii_analyzer.analyze(contract.parsed_text)
    anonymized = pii_analyzer.anonymize(contract.parsed_text, findings=findings)
    return {
        "contract_id": contract_id,
        "findings": findings,
        "has_pii": len(findings) > 0,
        "entity_types": list(dict.fromkeys(f["entity_type"] for f in findings)),
        "anonymized_preview": anonymized["anonymized"][:2000] if anonymized["has_pii"] else "",
    }

@router.get("/status")
async def pii_status():
    """Return PII service status and available recognizers.
    
    Does NOT trigger Presidio engine initialization to avoid blocking.
    """
    return {
        "presidio_installed": True,  # pip package is present
        "presidio_initialized": pii_analyzer._presidio_available is not None,
        "indian_patterns": list(pii_analyzer.INDIAN_PATTERNS.keys()),
        "version": "2.0",
    }
