# REXI MVP — Legal Process Automation Platform

A pre-seed MVP for India's mid-market legal tech stack. REXI combines **Contract Lifecycle Management (CLM)**, **AI-powered Risk Assessment**, and **Regulatory Intelligence** into a single platform backed by a Neo4j Knowledge Graph.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        REACT 18 + VITE                       │
│  Dashboard · Contracts · Risk · Regulatory · Knowledge Graph │
│  Playbook · Obligations · Calendar · Analytics · Settings   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                      FASTAPI BACKEND                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │  Contracts  │  │  Risk Engine │  │ Regulatory Intel    │ │
│  │  Router     │  │  (3-Layer)   │  │ Router + Scraper    │ │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│  ┌──────▼────────────────▼─────────────────────▼──────────┐ │
│  │              IN-MEMORY DB (pre-seed)                   │ │
│  │   Orgs · Contracts · Clauses · Playbooks · Alerts      │ │
│  │   Obligations · Templates · Audit Logs · Comments      │ │
│  │   Approval Stages · Notifications                      │ │
│  └────────────────────────┬───────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │           NEO4J KNOWLEDGE GRAPH (LOKG)                 │ │
│  │   Contracts ──Clauses──► Statutes / Regulations        │ │
│  │   Parties ──Obligations──► Contract Network            │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐ │
│  │           MINIO OBJECT STORAGE                         │ │
│  │   PDF contracts stored with presigned URLs             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Document Processing Pipeline (400-Page Contracts)

REXI uses a **production-grade document pipeline** designed for 400-page M&A contracts, infrastructure PPPs, and banking agreements.

```
PDF Upload
    │
    ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Docling        │────▶│  Hierarchical   │────▶│  Chunk-Aware    │
│  (IBM)          │     │  Chunking       │     │  Clause         │
│  Layout-aware   │     │  Legal hierarchy│     │  Extraction     │
│  TableFormer    │     │  Parent-child   │     │  GPT-4o-mini    │
│  OCR fallback   │     │  Cross-references│    │  per-chunk      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                            ┌─────────────────┐
│  Tables +       │                            │  Deduplicated   │
│  Cross-refs     │                            │  Clauses        │
└─────────────────┘                            └─────────────────┘
```

### Why Docling?

| Tool | License | Best For | Why We Chose It |
|------|---------|----------|-----------------|
| **Docling** (IBM) | MIT ✅ | Enterprise RAG | Hierarchical chunking, TableFormer, semantic chunking, LangChain integration |
| Marker (DataLab) | CC-BY-NC-SA ⚠️ | Speed | **Non-commercial** — unusable for REXI |
| MinerU (OpenDataLab) | Apache-2.0 | Chinese docs | Good but Docling has better structure preservation |
| Unstructured-IO | Mixed | Cloud API | Expensive at scale, Docling is free |

### Chunking Strategy

For 400-page contracts, naive `full_text[:6000]` fails. REXI implements:

1. **Hierarchical chunking** — preserves legal hierarchy: Document → Article → Section 1.1 → Subsection 1.1(a) → Clause
2. **Parent-child linking** — each chunk knows its parent section
3. **Context enrichment** — each chunk includes "Article 1 > Section 1.2 > " prefix before extraction
4. **Cross-reference resolution** — detects "Section 4.2(a)" and links to target chunks
5. **Sliding windows** — overlapping chunk groups for context-aware processing
6. **Deduplication** — Jaccard similarity removes duplicate clauses across chunks
7. **Progressive summarization** — leaf → parent → document summaries

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- (Optional) OpenAI API key for GPT-4o-mini clause extraction
- **Note**: Docling downloads ~1GB of models on first run

### 1. Start
```bash
cd rexi-mvp
./start.sh
```

Or manually:
```bash
docker compose up -d neo4j minio
sleep 10
docker compose up -d backend frontend
```

### 2. Add OpenAI Key (Optional)
Edit `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```
> Without an OpenAI key, the system uses **Legal-BERT** + rule-based extraction.

### 3. Access
| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 (neo4j / rexi_neo4j_2025) |
| MinIO Console | http://localhost:9001 (rexi_minio / rexi_minio_secret) |

---

## What Works Out of the Box

### Pillar 1 — CLM
- **Multi-file batch upload** with per-file progress
- **Docling-based extraction** — layout-aware, table extraction, OCR fallback
- **Hierarchical chunking** for 400-page contracts
- **AI clause extraction: GPT-4o-mini → Legal-BERT → rule-based fallback** (chunk-aware)
- **Entity extraction** (parties, governing law, value, dates, auto-renewal)
- **Cross-reference detection** (Section 4.2(a), Clause 5.3)
- **Contract list with search, filter by type**
- **Detail view with 8 tabs**: Overview, Clauses, **Document Map**, Risk, Obligations, Approvals, Comments, PDF Viewer
- **MinIO object storage** with presigned PDF URLs
- **Obligation auto-extraction** from contract text
- **Contract template library** (Vendor Agreement, Employment, NDA)
- **Approval workflow** (Draft → In Review → Approved → Signed → Active)
- **Comment system** on contracts and clauses

### Pillar 2 — AI Risk Assessment (3-Layer)
- **Playbook Layer (35%)**: Per-company rules via visual rule builder
- **Law Layer (40%)**: Indian Contract Act, DPDP Act, SEBI LODR enforceability benchmarks
- **Regulatory Layer (25%)**: Real-time regulatory gap detection
- Overall risk score + severity-classified findings
- Suggested amendments + statute references per finding
- **Risk report export** — downloadable HTML report
- **Playbook Management UI**: Create / edit / delete rules with 14 clause types

### Pillar 3 — Regulatory Intelligence
- 5 seeded regulatory updates (DPDP May 2027, Labour Codes Nov 2025, MCA V3, RBI NPA, SEBI LODR)
- **RSS scraper** for RBI, SEBI, MCA, Labour Ministry, GST, DPIIT
- Per-organization alert generation with auto contract impact analysis
- Priority-based alert classification (critical / high / medium / low)
- **Regulatory scrape endpoint** (`POST /api/v1/regulatory/scrape`)

### Knowledge Graph (Neo4j)
- Contract → Clause → Statute relationships
- Contract → Party relationships
- Contract → Obligation relationships
- Regulation → ClauseType → Contract impact queries
- **Interactive vis-network graph visualization**
- Organization → Contract network summaries
- 10 seeded Indian statutes + 5 regulations

### Analytics & Reporting
- **4 recharts visualizations**: Findings by Severity (Pie), Findings by Type (Bar), Contract Status (Pie), Volume Trend (Line)
- **Calendar / Renewal tracking**: Upcoming renewals, expired contracts, obligation deadlines
- **Audit logs**: Every contract upload, risk assessment, regulatory scan
- **Obligations tracker**: Dashboard KPIs + mark-as-done

---

## Seeded Demo Data

| Entity | Count |
|--------|-------|
| Demo Organization | 1 (Acme Manufacturing Pvt Ltd) |
| Playbook Rules | 6 |
| Enforceability Benchmarks | 10 |
| Regulatory Updates | 5 |
| Regulatory Alerts | 5 |
| Contract Templates | 3 |
| Sample Obligations | 4 |
| Sample Audit Logs | 3 |
| Neo4j Statutes | 10 |
| Neo4j Regulations | 5 |

---

## API Endpoints

### Contracts
```
POST /api/v1/contracts/upload                # Upload PDF (Docling pipeline)
GET  /api/v1/contracts                       # List + search/filter
GET  /api/v1/contracts/{id}                  # Detail with chunks, clauses, risk, obligations, pdf_url
GET  /api/v1/contracts/{id}/pdf              # PDF download / presigned URL
POST /api/v1/contracts/{id}/assess           # Re-run risk assessment
```

### Risk
```
GET  /api/v1/risk/dashboard                  # Risk KPIs
GET  /api/v1/risk/findings                   # All findings
PUT  /api/v1/risk/findings/{id}/resolve      # Resolve finding
```

### Playbook
```
GET  /api/v1/playbook/rules                  # List rules
POST /api/v1/playbook/rules                  # Create rule
PUT  /api/v1/playbook/rules/{id}             # Update rule
DEL  /api/v1/playbook/rules/{id}             # Delete rule
```

### Regulatory
```
GET  /api/v1/regulatory/alerts               # List alerts
PUT  /api/v1/regulatory/alerts/{id}/acknowledge
GET  /api/v1/regulatory/alerts/unread-count
GET  /api/v1/regulatory/updates              # Regulatory updates
GET  /api/v1/regulatory/dashboard            # Regulatory KPIs
POST /api/v1/regulatory/scrape               # Trigger RSS scraping
```

### Obligations
```
GET  /api/v1/obligations                     # List obligations
GET  /api/v1/obligations/dashboard/summary   # Obligations KPIs
PUT  /api/v1/obligations/{id}/status         # Update status
```

### Templates
```
GET  /api/v1/templates                       # List templates
POST /api/v1/templates                       # Create template
```

### Knowledge Graph
```
GET  /api/v1/graph/contracts/{id}/network    # Contract KG network
GET  /api/v1/graph/regulation-impact/{id}    # Affected contracts
GET  /api/v1/graph/org/{id}/contracts        # Org contract summary
```

### Audit
```
GET  /api/v1/audit/logs                      # All automation logs
GET  /api/v1/audit/logs/recent?limit=10      # Recent logs
```

### Approvals
```
GET  /api/v1/approvals/contracts/{id}/stages # Approval stages
POST /api/v1/approvals/contracts/{id}/submit # Submit for approval
PUT  /api/v1/approvals/stages/{id}/approve   # Approve stage
PUT  /api/v1/approvals/stages/{id}/reject    # Reject stage
POST /api/v1/approvals/contracts/{id}/transition # Change status
```

### Comments
```
GET  /api/v1/comments/contracts/{id}         # List comments
POST /api/v1/comments/contracts/{id}         # Add comment
DEL  /api/v1/comments/{id}                   # Delete comment
```

### Notifications
```
GET  /api/v1/notifications                   # List notifications
GET  /api/v1/notifications/unread-count
PUT  /api/v1/notifications/{id}/read
PUT  /api/v1/notifications/read-all
```

### Reports
```
GET  /api/v1/reports/contracts/{id}/risk     # Generate HTML risk report
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Vite, Tailwind CSS, Lucide React, vis-network, recharts |
| Backend | FastAPI, Pydantic v2, Uvicorn |
| Document Processing | **Docling** (IBM) — layout analysis, TableFormer, hierarchical chunking |
| AI | GPT-4o-mini (OpenAI), Legal-BERT (nlpaueb/legal-bert-base-uncased), rule-based fallback |
| PDF | Docling (primary), PyMuPDF (fallback), pdfplumber (tables) |
| Graph DB | Neo4j 5.15 Community (APOC + GDS) |
| Object Store | MinIO |
| In-Memory DB | Python dicts (swap to PostgreSQL for production) |

---

## Path to Production

1. **Swap DB**: Replace `InMemoryDB` with PostgreSQL + SQLAlchemy + Alembic
2. **Add Auth**: OAuth2 / JWT with organization scoping
3. **Legal-BERT Fine-tuning**: Train on Indian contract corpus for +23pp accuracy
4. **RSS Feeds**: Wire real RSS feeds for RBI, SEBI, MCA, Labour Ministry
5. **Leegalty**: Integrate e-signature API
6. **On-Premise**: Containerized deployment script for customer infrastructure
7. **Vector Search**: Add Pinecone/Weaviate for semantic contract search

---

## Investment Context

This MVP demonstrates the three integrated pillars described in the REXI Investment Thesis:
- **CLM** as the entry point with template library + obligation tracking + approval workflow
- **AI Risk Assessment** as the differentiation with 3-layer scoring + playbook engine + chunk-aware extraction
- **Regulatory Intelligence** as the retention engine with RSS scraping + auto-alerts
- **Knowledge Graph** as the 36-month moat with interactive visualization
- **Document Processing** as the technical barrier with Docling-based hierarchical chunking

Built to validate product-market fit with 10 pilot customers on a ₹60 lakh pre-seed budget.
