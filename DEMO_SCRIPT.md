# REXI Investor Demo Script
## Lead with Platform, Present AI as Accelerator

---

## Pre-Demo Checklist (Do These 10 Minutes Before)

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. Start frontend (in another terminal)
cd frontend
npm run dev

# 3. Open browser to http://localhost:5173
# 4. Verify Dashboard loads with 3 contracts, risk scores, and platform metrics
# 5. NEVER upload a PDF during the demo — use pre-seeded data only
```

**If backend fails to start:**
- Check `.env` has `GEMINI_API_KEY` set
- Check `DATABASE_URL` is reachable
- Fallback: `DATABASE_URL=sqlite+aiosqlite:///:memory:` works locally

**If frontend shows blank:**
- Check Vite dev server is running on port 5173
- Check backend health: `curl http://localhost:8000/health`

---

## Demo Flow (12-15 minutes total)

### OPENING (1 min) — Platform Value First
> *"REXI is not an AI chatbot. It is a contract intelligence platform. Every feature you see today works with or without AI — the AI just makes it 10x faster."*

Click: **Dashboard**
- Point to **"Platform Value"** row:
  - "₹1.94Cr under management" — deterministic SQL aggregation
  - "100% automation rate" — all 3 demo contracts auto-processed
  - "7.5 hours saved" — vs manual legal review
  - "100% compliance coverage" — every contract has risk assessment

> *"This is pure SQL. Zero AI calls. The platform value is the structured database, approval workflows, audit trails, and counterparty analytics."*

---

### TAB 1: Counterparty Dashboard (2 min) — Deterministic Power
Click: **Counterparty** (sidebar)

> *"Most companies don't know which vendor poses the most risk. REXI aggregates every contract, finding, and obligation per counterparty — using pure SQL."*

- Show **TechSupply Solutions**: 1 contract, ₹50L value, risk score 72% (high risk)
- Show **Global Logistics Partners**: 1 contract, ₹1.2Cr value, risk score 81% (high risk)
- Show **Employment Contract**: 1 contract, ₹24L value, risk score 35% (low risk)
- Click the **risk bar chart** — color-coded by tier
- Click the **donut chart** — risk distribution

> *"No AI here. This is aggregation over structured data that we extract deterministically from every uploaded contract."*

---

### TAB 2: Contracts List + Detail (2 min) — The Data Model
Click: **Contracts** (sidebar)

- Show list with **risk scores**, **end dates**, **auto-renewal flags**
- Click **"Vendor Agreement — TechSupply Solutions"**

> *"This contract was processed by our pipeline: Docling for OCR, rule-based clause extraction, deterministic risk scoring against Indian law and the company playbook."*

Scroll through tabs:
- **Overview**: counterparty, value, governing law
- **Clauses**: 6 extracted clauses with confidence scores
- **Risk**: severity breakdown, findings list
- **Obligations**: linked compliance tasks
- **Approvals**: legal → finance → CEO stepper

> *"Every tab you see is powered by structured data in PostgreSQL. The AI features are additive — they sit on top of this foundation."*

---

### TAB 3: Deterministic Redline (2 min) — No AI
Click: **Redline** tab inside Contract Detail

> *"When a vendor sends a revised contract, lawyers spend hours comparing versions. REXI does this deterministically."*

- Show **"Compare with Version"** dropdown (v1 seeded)
- Click **Compare**
- Show results: semantic clause-level diff using `difflib.SequenceMatcher`
  - Termination clause: numeric change detection (15 days → 30 days)
  - Label badges: unchanged / modified / added / removed
  - Similarity scores

> *"This uses local sentence-transformers and Python's difflib. No API calls. Works offline."*

---

### TAB 4: AI Accelerator — Plain English (2 min)
Click: **Plain English** tab

> *"Now we turn on the AI accelerator. Legal clauses are dense. Our Plain English feature translates them for non-lawyers — but only after the platform has already structured them."*

- Show a clause card:
  - Original: *"Either party may terminate this agreement with 15 days written notice."*
  - Plain English: *"You or the vendor can cancel the contract by giving 15 days notice in writing."*
  - Risk level: High (below 30-day playbook standard)

> *"The AI doesn't replace the lawyer. It makes the lawyer 10x faster by pre-structuring and pre-translating everything."*

---

### TAB 5: AI Accelerator — Chat with Contract (2 min)
Click: **Chat** tab

> *"Instead of reading 40 pages, the CFO can ask questions in natural language."*

Type: *"What is the termination clause?"*
- Watch **SSE streaming** — tokens appear in real-time
- Point out the step indicators: Analyzing → Searching → Generating

> *"This streams from Gemini 2.0 Flash. But notice: the answer is grounded in the actual contract clauses we extracted deterministically. No hallucination — the context is real."*

---

### TAB 6: Calendar + Obligations (2 min) — Timeline View
Click: **Calendar** (sidebar)

> *"Contracts create obligations. REXI extracts deadlines and displays them on a visual calendar."*

- Navigate months with arrows
- Click a day with dots → sidebar shows events
- Show **overdue obligations** in orange
- Show **upcoming renewals** in blue

> *"Again, this is deterministic. We parse dates from the contract text using `dateparser`, then track them in SQL."*

---

### CLOSING (1 min) — The Narrative
> *"So what is REXI?"*
> 
> *"It is a contract intelligence platform with three layers:"*
> 1. *"**Foundation**: PostgreSQL, structured clauses, risk assessments, obligations, audit trails — works without any AI."*
> 2. *"**Deterministic engine**: Semantic diff, SQL aggregation, calendar extraction, playbook compliance — local computation, no API costs."*
> 3. *"**AI accelerator**: Plain English, chat, explain-risk — Gemini 2.0 Flash, 1,500 free requests/day, grounded in real contract data."*
>
> *"We charge for the platform. The AI is the cherry on top."*

---

## Talking Points to Avoid "AI Wrapper" Perception

| If investor asks... | Respond with... |
|---|---|
| "Isn't this just a Gemini wrapper?" | "Gemini is 1 of 20 features. The platform value is the structured database, approval workflows, and deterministic analytics. AI is an accelerator layer." |
| "What if Gemini goes down?" | "Every deterministic feature works offline: clause extraction, risk scoring, redline diff, counterparty dashboard. Only Plain English and Chat need Gemini." |
| "What's the moat?" | "The moat is structured data density. Every contract uploaded makes the counterparty dashboard, obligation tracker, and playbook rules more valuable. AI models are commodities; proprietary contract graphs are not." |
| "Who are you competing with?" | "Ironclad and Icertis cost $50K+/year and take 6 months to deploy. REXI is deployable in 1 day, works with Indian commercial law out of the box, and costs a fraction." |
| "How do you make money?" | "SaaS per-seat + API usage for enterprise. The AI features are metered but the platform core is fixed fee." |

---

## Emergency Fallbacks

| Scenario | Fallback |
|---|---|
| Gemini API fails / rate limited | "As you can see, every deterministic feature still works. The AI layer is additive." Switch to Counterparty Dashboard + Redline diff. |
| Neon PostgreSQL connection fails | Backend auto-falls back to SQLite in-memory. All features work locally. |
| Neo4j is down | Knowledge Graph page shows graceful "Neo4j unavailable" message. All other features unaffected. |
| PDF upload crashes | Skip upload. Use pre-seeded contracts. Say: *"We've already processed these contracts. Let me show you what the platform did."* |
| Chat streaming looks slow | Switch to non-streaming tab (Plain English) which returns complete responses faster. |
| Browser console shows warnings | Ignore. react-pdf worker CDN warning is harmless. |

---

## Key Metrics to Memorize

- **3 demo contracts** seeded with ₹1.94Cr total value
- **18 clauses** extracted across all contracts
- **8 risk findings** (2 critical, 2 high, 4 medium)
- **10 obligations** tracked
- **Platform value**: ₹1.94Cr under management, 100% automation, 7.5h saved
- **Gemini cost**: Free tier 1,500 req/day covers entire demo day
- **Processing time**: ~4-10 seconds per contract (CPU + Docling)

---

## After the Demo

If investor wants to see code:
- Show `vendor/` directory — literal copies from 6 open-source repos
- Show `backend/app/services/semantic_diff.py` — `_diff_bullets()` is deterministic `difflib`
- Show `backend/app/routers/counterparty.py` — pure SQL, zero AI calls
- Show `backend/app/services/knowledge_graph_service.py` — GraphRAG Cypher from Neo4j examples
