"""PDF clause highlighting router.
Generates bounding boxes for clauses using pdfplumber text extraction.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from app.core.database import get_session
from app.models.tables import Contract, ContractClause, ClauseHighlight

router = APIRouter(prefix="/api/v1/highlights", tags=["highlights"])


@router.get("/contracts/{contract_id}")
async def get_highlights(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Get all clause highlights for a contract."""
    result = await session.execute(
        select(ClauseHighlight).where(ClauseHighlight.contract_id == contract_id)
    )
    highlights = result.scalars().all()

    # Fetch clause texts for enrichment
    clause_ids = [h.clause_id for h in highlights if h.clause_id]
    clause_map = {}
    if clause_ids:
        res = await session.execute(select(ContractClause).where(ContractClause.id.in_(clause_ids)))
        clause_map = {c.id: c for c in res.scalars().all()}

    return {
        "contract_id": contract_id,
        "highlights": [
            {
                "id": h.id,
                "clause_id": h.clause_id,
                "clause_type": h.clause_type,
                "clause_text": clause_map.get(h.clause_id, {}).clause_text if h.clause_id in clause_map else "",
                "page_number": h.page_number,
                "bounding_box": {
                    "x": h.x,
                    "y": h.y,
                    "width": h.width,
                    "height": h.height,
                    "color": h.color,
                },
            }
            for h in highlights
        ]
    }


@router.post("/contracts/{contract_id}/generate")
async def generate_highlights(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Generate highlights by searching clause text in the PDF.
    Uses pdfplumber to find bounding boxes.
    """
    import os
    import pdfplumber

    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.pdf_path or not os.path.exists(contract.pdf_path):
        raise HTTPException(status_code=400, detail="PDF not available")

    res_clauses = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
    clauses = res_clauses.scalars().all()

    # Color map per clause type
    color_map = {
        "termination": "rgba(239, 68, 68, 0.3)",
        "liability": "rgba(249, 115, 22, 0.3)",
        "indemnity": "rgba(245, 158, 11, 0.3)",
        "payment": "rgba(34, 197, 94, 0.3)",
        "confidentiality": "rgba(59, 130, 246, 0.3)",
        "governing_law": "rgba(139, 92, 246, 0.3)",
        "intellectual_property": "rgba(236, 72, 153, 0.3)",
        "force_majeure": "rgba(107, 114, 128, 0.3)",
        "default": "rgba(255, 179, 0, 0.3)",
    }

    generated = []
    with pdfplumber.open(contract.pdf_path) as pdf:
        for cl in clauses:
            # Search for clause text in PDF
            # Use first 50 chars as search key to avoid missing due to OCR errors
            search_text = cl.clause_text[:80].strip()
            if len(search_text) < 10:
                continue

            found = False
            for page_idx, page in enumerate(pdf.pages):
                if found:
                    break
                words = page.extract_words()
                # Simple approach: look for a window of words matching the start of clause text
                text_words = search_text.split()
                if len(text_words) < 3:
                    continue

                # Look for first 3 words match
                first_three = text_words[:3]
                for i, w in enumerate(words):
                    if i + 2 >= len(words):
                        continue
                    window = [words[i+j]["text"] for j in range(3)]
                    if window == first_three:
                        # Found match — create bounding box from surrounding words
                        # Take a window of words around the match
                        start = max(0, i - 2)
                        end = min(len(words), i + 20)
                        match_words = words[start:end]

                        xs = [w["x0"] for w in match_words]
                        ys = [w["top"] for w in match_words]
                        x1s = [w["x1"] for w in match_words]
                        y1s = [w["bottom"] for w in match_words]

                        x = min(xs)
                        y = min(ys)
                        w = max(x1s) - x
                        h = max(y1s) - y

                        # Normalize to 0-1 based on page dimensions
                        pw, ph = page.width, page.height
                        if pw > 0 and ph > 0:
                            highlight = ClauseHighlight(
                                contract_id=contract_id,
                                clause_id=cl.id,
                                clause_type=cl.clause_type,
                                page_number=page_idx + 1,
                                x=round(x / pw, 4),
                                y=round(y / ph, 4),
                                width=round(w / pw, 4),
                                height=round(h / ph, 4),
                                color=color_map.get(cl.clause_type, color_map["default"]),
                            )
                            session.add(highlight)
                            generated.append(highlight)
                            found = True
                            break

    await session.commit()
    return {
        "contract_id": contract_id,
        "generated": len(generated),
        "highlights": [
            {
                "id": h.id,
                "clause_type": h.clause_type,
                "page_number": h.page_number,
                "x": h.x, "y": h.y,
                "width": h.width, "height": h.height,
                "color": h.color,
            }
            for h in generated
        ]
    }
