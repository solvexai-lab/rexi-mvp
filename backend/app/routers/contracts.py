"""Enhanced contracts router with Docling-based processing for 400-page contracts."""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
import os, shutil, time, asyncio
from app.core.database import get_session
from app.models.tables import Contract, ContractClause, ContractVersion, Obligation, AutomationLog, ContractTreeIndex, ContractEmbedding, PlaybookRule
from app.services.docling_processor import docling_processor
from app.services.chunking_service import chunking_service
from app.services.clause_extractor_v2 import chunked_clause_extractor
from app.services.knowledge_graph_service import kg_service
from app.services.storage import storage_service
from app.services.pii_service import pii_analyzer
from app.services.pageindex_service import pageindex_service
from app.services.playbook_evaluator import evaluate_contract

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

class ContractUpdate(BaseModel):
    title: str | None = None
    contract_type: str | None = None
    status: str | None = None
    counterparty_name: str | None = None
    counterparty_email: str | None = None
    governing_law: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    auto_renewal: bool | None = None
    value_inr: float | None = None

def _safe_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent path traversal."""
    import re
    base = os.path.basename(filename)
    safe = re.sub(r'[^\w\-.]', '_', base)
    return safe[:200] or "upload"


@router.post("/upload")
async def upload_contract(file: UploadFile = File(...), org_id: str = Form("demo-org")):
    start_time = time.time()

    # Enforce max file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {MAX_FILE_SIZE / (1024*1024)} MB")
    await file.seek(0)

    upload_dir = os.environ.get("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = _safe_filename(file.filename or "upload")
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # === PHASE 1: Ingest — short DB transaction ===
    from app.core.database import async_session_factory
    async with async_session_factory() as session:
        contract = Contract(org_id=org_id, title=safe_name, pdf_path=file_path, status="processing")
        session.add(contract)
        await session.commit()
        await session.refresh(contract)
        contract_id = contract.id

    # === PHASE 2: Heavy lifting — NO DB session ===
    try:
        process_result = docling_processor.process(file_path)
        chunks = process_result.get("chunks", [])
        tables = process_result.get("tables", [])
        cross_refs = process_result.get("cross_references", [])
        page_count = process_result.get("page_count", 1)

        clauses = await chunked_clause_extractor.extract_from_chunks(chunks)
        entities = await chunked_clause_extractor.extract_entities_from_chunks(chunks)
        obligations = await chunked_clause_extractor.extract_obligations_from_chunks(chunks)

        counterparty_name = ""
        governing_law = ""
        value_inr = 0
        auto_renewal = False
        start_date = None
        end_date = None
        if entities:
            counterparty_name = entities.get("parties", [{}])[0].get("name", "") if isinstance(entities.get("parties"), list) else ""
            governing_law = entities.get("governing_law", "")
            value_inr = float(entities.get("value_inr", 0)) if entities.get("value_inr") else 0
            auto_renewal = bool(entities.get("auto_renewal", False))
            start_date = entities.get("start_date")
            end_date = entities.get("end_date")
    except Exception as e:
        # Mark as failed so user knows upload didn't work
        async with async_session_factory() as session:
            result = await session.execute(select(Contract).where(Contract.id == contract_id))
            contract = result.scalar_one_or_none()
            if contract:
                contract.status = "failed"
                await session.commit()
        raise HTTPException(status_code=422, detail=f"Processing failed: {str(e)}")

    # === PHASE 3: Persist results — short DB transaction ===
    async with async_session_factory() as session:
        # Update contract
        result = await session.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one()
        contract.parsed_text = process_result.get("full_text", "")
        contract.status = "analyzed"
        contract.counterparty_name = counterparty_name
        contract.governing_law = governing_law
        contract.value_inr = value_inr
        contract.auto_renewal = auto_renewal
        contract.start_date = start_date
        contract.end_date = end_date

        # Save clauses
        for c in clauses:
            cl = ContractClause(contract_id=contract_id, **c)
            session.add(cl)
        await session.flush()

        # Snapshot as version 1
        version = ContractVersion(
            contract_id=contract_id,
            version_number=1,
            title=contract.title,
            pdf_path=file_path,
            parsed_text=process_result.get("full_text", ""),
            created_by="system"
        )
        session.add(version)
        await session.flush()

        # Save obligations + KG
        for ob in obligations:
            obligation = Obligation(
                contract_id=contract_id, org_id=org_id,
                description=ob.get("description", ""),
                obligation_type=ob.get("type", "compliance"),
                due_date=ob.get("due_date"),
                status="pending"
            )
            session.add(obligation)
            await session.flush()
            await asyncio.to_thread(
                kg_service.create_obligation_node, obligation.id, obligation.description, obligation.obligation_type, obligation.due_date or ""
            )
            await asyncio.to_thread(kg_service.link_contract_obligation, contract_id, obligation.id)

        # KG links (legacy REXI schema)
        await asyncio.to_thread(kg_service.link_org_contract, org_id, contract_id)
        await asyncio.to_thread(
            kg_service.create_contract_node, contract_id, contract.title, contract.contract_type, contract.status, governing_law, value_inr
        )
        res = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
        stored_clauses = res.scalars().all()
        for cl in stored_clauses:
            await asyncio.to_thread(
                kg_service.create_clause_node, cl.id, cl.clause_type, cl.clause_text, cl.page_number, cl.confidence_score
            )
            await asyncio.to_thread(kg_service.link_contract_clause, contract_id, cl.id)

        # GraphRAG schema (literal Cypher from graphrag-contract)
        graphrag_clauses = []
        for idx, cl in enumerate(stored_clauses):
            excerpt_id = f"{contract_id}_clause_{cl.id}_excerpt_1"
            graphrag_clauses.append({
                "id": cl.id,
                "name": cl.clause_type,
                "type": cl.clause_type,
                "page": cl.page_number or 1,
                "excerpts": [
                    {
                        "id": excerpt_id,
                        "text": cl.clause_text[:2000],
                        "order": 1
                    }
                ]
            })
        await asyncio.to_thread(
            kg_service.create_graphrag_contract,
            agreement_id=contract_id,
            agreement_name=contract.title,
            language="en",
            effective_date=start_date or "2024-01-01",
            initial_term="12 months",
            renewal_term="12 months" if auto_renewal else "",
            inception_date=start_date or "2024-01-01",
            status=contract.status,
            country_name="India",
            governing_law_country=governing_law or "India",
            organization_name=org_id,
            organization_id=org_id,
            organization_address="",
            organization_role="signatory",
            clauses=graphrag_clauses,
        )

        # Audit Log
        duration_ms = int((time.time() - start_time) * 1000)
        log = AutomationLog(
            org_id=org_id, automation_type="contract_upload", status="completed",
            input_summary=file.filename,
            output_summary=f"{len(clauses)} clauses, {len(tables)} tables, {page_count} pages",
            duration_ms=duration_ms
        )
        session.add(log)
        await session.commit()

    # === PHASE 4: Enrichment layers (non-blocking, each wrapped) ===
    enrichment = await _run_enrichment_layers(
        contract_id=contract_id,
        org_id=org_id,
        safe_name=safe_name,
        process_result=process_result,
        clauses=clauses,
    )

    return {
        "contract_id": contract_id,
        "clauses_extracted": len(clauses),
        "tables_found": len(tables),
        "pages": page_count,
        "chunks": len(chunks),
        "cross_references": len(cross_refs),
        "obligations_found": len(obligations),
        "processing_time_ms": duration_ms,
        "extractor": process_result.get("extracted_by", "unknown"),
        "pii": enrichment.get("pii", {"has_pii": False, "count": 0}),
        "tree": enrichment.get("tree", {"has_tree": False, "node_count": 0}),
        "embeddings": enrichment.get("embeddings", {"indexed": 0}),
    }

@router.get("")
async def list_contracts(org_id: str = "demo-org", session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contract).where(Contract.org_id == org_id))
    contracts = result.scalars().all()

    # Batch enrichment lookups
    contract_ids = [c.id for c in contracts]
    tree_result = await session.execute(
        select(ContractTreeIndex.contract_id).where(ContractTreeIndex.contract_id.in_(contract_ids))
    )
    has_tree = {row[0] for row in tree_result.all()}

    emb_result = await session.execute(
        select(ContractEmbedding.contract_id).where(ContractEmbedding.contract_id.in_(contract_ids))
    )
    emb_counts: dict[str, int] = {}
    for cid in emb_result.scalars().all():
        emb_counts[cid] = emb_counts.get(cid, 0) + 1

    return [{"id": c.id, "title": c.title, "contract_type": c.contract_type,
             "status": c.status, "counterparty_name": c.counterparty_name,
             "value_inr": c.value_inr, "risk_score": c.risk_score,
             "end_date": c.end_date, "auto_renewal": c.auto_renewal,
             "has_tree": c.id in has_tree,
             "embedding_count": emb_counts.get(c.id, 0),
             "has_parsed_text": bool(c.parsed_text),
             } for c in contracts]

@router.get("/{contract_id}")
async def get_contract(contract_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")

    res_clauses = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
    clauses = res_clauses.scalars().all()

    res_obligations = await session.execute(select(Obligation).where(Obligation.contract_id == contract_id))
    obligations = res_obligations.scalars().all()

    pdf_url = None
    if c.pdf_path and not c.pdf_path.startswith("./"):
        try:
            pdf_url = storage_service.get_presigned_url(c.pdf_path)
        except Exception:
            pass

    contract_data = c.model_dump()
    contract_data["pdf_url"] = pdf_url
    return {
        "contract": contract_data,
        "clauses": [cl.model_dump() for cl in clauses],
        "assessment": None,
        "findings": [],
        "obligations": [o.model_dump() for o in obligations],
        "chunks": []
    }

@router.api_route("/{contract_id}/pdf", methods=["GET", "HEAD"])
async def get_contract_pdf(contract_id: str, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    if c.pdf_path and c.pdf_path.startswith("./"):
        return FileResponse(c.pdf_path, media_type="application/pdf", filename=c.title)
    try:
        url = storage_service.get_presigned_url(c.pdf_path, expires=300)
        if url:
            return {"pdf_url": url}
    except Exception:
        pass
    upload_dir = os.environ.get("UPLOAD_DIR", "./uploads")
    local_path = os.path.join(upload_dir, c.title)
    if os.path.exists(local_path):
        return FileResponse(local_path, media_type="application/pdf", filename=c.title)
    raise HTTPException(status_code=404, detail="PDF not found")


@router.get("/{contract_id}/playbook-evaluation")
async def evaluate_contract_playbook(
    contract_id: str,
    org_id: str = "demo-org",
    session: AsyncSession = Depends(get_session)
):
    """Evaluate a contract against the organization's playbook rules."""
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    res_clauses = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
    clauses = [cl.model_dump() for cl in res_clauses.scalars().all()]

    res_rules = await session.execute(
        select(PlaybookRule).where(PlaybookRule.org_id == org_id, PlaybookRule.is_active == True)
    )
    rules = res_rules.scalars().all()

    evaluation = evaluate_contract(
        contract_type=contract.contract_type or "vendor",
        clauses=clauses,
        rules=rules,
    )
    return evaluation


async def _run_enrichment_layers(contract_id: str, org_id: str, safe_name: str, process_result: dict, clauses: list) -> dict:
    """Run all enrichment layers with graceful degradation.
    
    Each layer is independent — failure in one does not affect others.
    Returns a dict with results from each layer.
    """
    from app.core.database import async_session_factory
    from app.models.tables import ContractEmbedding
    from app.routers.embeddings import _get_embedding

    results = {
        "pii": {"has_pii": False, "entity_types": [], "count": 0},
        "tree": {"has_tree": False, "node_count": 0},
        "embeddings": {"indexed": 0},
    }

    # Layer 1: PII scan
    try:
        full_text = process_result.get("full_text", "")
        if full_text:
            pii_findings = pii_analyzer.analyze(full_text)
            results["pii"] = {
                "has_pii": len(pii_findings) > 0,
                "entity_types": list(dict.fromkeys(f["entity_type"] for f in pii_findings)),
                "count": len(pii_findings),
            }
    except Exception:
        pass

    # Layer 2: PageIndex tree
    try:
        markdown_text = process_result.get("full_text", "")
        if markdown_text and len(markdown_text) > 500:
            tree_data = pageindex_service.build_tree_from_markdown(
                markdown_text,
                doc_name=safe_name,
                add_summaries=False,
            )
            if tree_data.get("structure"):
                node_count = len(pageindex_service.flatten_tree(tree_data))
                async with async_session_factory() as session:
                    tree_index = ContractTreeIndex(
                        contract_id=contract_id,
                        org_id=org_id,
                        doc_name=tree_data.get("doc_name", safe_name),
                        structure=tree_data.get("structure", []),
                        line_count=tree_data.get("line_count", 0),
                        node_count=node_count,
                    )
                    session.add(tree_index)
                    await session.commit()
                results["tree"] = {"has_tree": True, "node_count": node_count}
    except Exception:
        pass

    # Layer 3: Embedding indexing (auto-generate for clauses)
    try:
        indexed = 0
        async with async_session_factory() as session:
            for cl in clauses:
                existing = await session.execute(
                    select(ContractEmbedding).where(
                        ContractEmbedding.contract_id == contract_id,
                        ContractEmbedding.chunk_text == cl.get("clause_text", "")[:500],
                    )
                )
                if existing.scalar_one_or_none():
                    continue
                try:
                    emb, emb_name = await _get_embedding(cl.get("clause_text", ""))
                    ce = ContractEmbedding(
                        contract_id=contract_id,
                        chunk_text=cl.get("clause_text", "")[:500],
                        embedding=emb,
                        page_number=cl.get("page_number", 1),
                        embedder=emb_name,
                    )
                    session.add(ce)
                    indexed += 1
                except Exception:
                    continue
            await session.commit()
        results["embeddings"] = {"indexed": indexed}
    except Exception:
        pass

    return results


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str, session: AsyncSession = Depends(get_session)):
    """Delete a contract and all related data."""
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Delete related records
    from sqlmodel import delete
    await session.execute(delete(ContractClause).where(ContractClause.contract_id == contract_id))
    await session.execute(delete(ContractVersion).where(ContractVersion.contract_id == contract_id))
    await session.execute(delete(Obligation).where(Obligation.contract_id == contract_id))
    await session.execute(delete(ContractTreeIndex).where(ContractTreeIndex.contract_id == contract_id))
    await session.execute(delete(ContractEmbedding).where(ContractEmbedding.contract_id == contract_id))

    # Delete PDF file
    if contract.pdf_path and os.path.exists(contract.pdf_path):
        try:
            os.remove(contract.pdf_path)
        except Exception:
            pass

    await session.delete(contract)
    await session.commit()
    return {"deleted": True, "contract_id": contract_id}


@router.put("/{contract_id}")
async def update_contract(contract_id: str, data: ContractUpdate, session: AsyncSession = Depends(get_session)):
    """Update contract metadata."""
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    await session.commit()
    await session.refresh(contract)
    return contract
