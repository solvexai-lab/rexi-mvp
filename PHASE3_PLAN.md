# REXI Phase 3: Contract Intelligence Engine
## Final Build Plan — Updated with 3-Pillar Knowledge Graph

---

## The 3-Pillar Architecture

Everything lives in Neo4j. All three pillars are first-class graph citizens.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEO4J GRAPH SCHEMA (3 PILLARS)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PILLAR 1: PLAYBOOK (Organization-defined rules)                   │
│  ─────────────────────────────────────────────────                 │
│  (PlaybookRule {id, rule_name, rule_type, condition,              │
│                 threshold_value, severity, org_id})                │
│       ↑                                                             │
│       └─[:VIOLATED_BY]──────(Clause {clause_type, text})          │
│                               ↑                                     │
│                               └─[:IN]──(Contract {title, status})  │
│                                                                     │
│  PILLAR 2: LAW (Statutes, case law, enforceability)                │
│  ───────────────────────────────────────────────────               │
│  (Statute {id, act_name, section, enforceability_score,           │
│            conditions, section_text})                              │
│       ↑                                                             │
│       └─[:GOVERNS]──────────(Clause {clause_type, text})          │
│                               ↑                                     │
│                               └─[:IN]──(Contract {title, status})  │
│                                                                     │
│  PILLAR 3: REGULATORY (Updates, alerts, compliance deadlines)      │
│  ───────────────────────────────────────────────────────────       │
│  (Regulation {id, title, source, effective_date, summary})         │
│       ↑                                                             │
│       └─[:AFFECTS_CLAUSE_TYPE]────(ClauseType {type})             │
│                                       ↑                             │
│                                       └─[:HAS_TYPE]──(Clause)      │
│                                                         ↑           │
│                                                         └─[:IN]────(Contract)
│                                                                     │
│  CORE ENTITIES                                                      │
│  ─────────────                                                      │
│  (Organization {id, name, industry})                                │
│       └─[:HAS_CONTRACT]──(Contract)                                 │
│                                                                     │
│  (Party {id, name, email, party_type})                              │
│       ↑                                                             │
│       └─[:PARTY_TO]──(Contract)                                     │
│                                                                     │
│  (Obligation {id, description, due_date, status})                   │
│       ↑                                                             │
│       └─[:BELONGS_TO]──(Contract)                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Day 2 Updated: 3-Pillar Graph + Auto-Detect Simulation

### Morning: Graph Schema + Seeding (4 hours)

#### 1. Neo4j Docker Setup
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/rexi2025 \
  -e NEO4J_PLUGINS='["apoc", "gds"]' \
  -e NEO4J_dbms_memory_heap_max__size=1G \
  neo4j:5.15-community
```

#### 2. Seed All 3 Pillars

**Pillar 1: Playbook Rules (from PostgreSQL → Neo4j)**
```cypher
// Create playbook rules
CREATE (r1:PlaybookRule {
  id: "rule-1", org_id: "demo-org",
  rule_name: "Max Liability Cap", rule_type: "liability",
  condition: "max_value", threshold_value: "2000000",
  severity: "high", is_active: true
})
CREATE (r2:PlaybookRule {
  id: "rule-2", org_id: "demo-org",
  rule_name: "Min Termination Notice", rule_type: "termination",
  condition: "min_value", threshold_value: "30",
  severity: "critical", is_active: true
})
// ... seed all 6 rules
```

**Pillar 2: Law / Statutes**
```cypher
CREATE (s1:Statute {
  id: "ica-s10", act_name: "Indian Contract Act, 1872",
  section: "Section 10", section_text: "What agreements are contracts.",
  enforceability_score: 0.95,
  conditions: "Must be a lawful agreement with competent parties."
})
CREATE (s2:Statute {
  id: "ica-s56", act_name: "Indian Contract Act, 1872",
  section: "Section 56", section_text: "Agreement to do impossible act is void.",
  enforceability_score: 0.90,
  conditions: "Must be explicit and reasonable."
})
CREATE (s3:Statute {
  id: "dpdp-s12", act_name: "DPDP Act, 2023",
  section: "Section 12", section_text: "Consent requirement for data processing.",
  enforceability_score: 0.92,
  conditions: "Consent must be free, specific, informed."
})
// ... seed all 10 statutes
```

**Pillar 3: Regulations**
```cypher
CREATE (reg1:Regulation {
  id: "dpdp-may2027", title: "DPDP Compliance Deadline May 2027",
  source: "DPDP Board", effective_date: "2027-05-13",
  summary: "All data fiduciaries must comply by May 2027. Penalty up to 250 Cr."
})
CREATE (reg2:Regulation {
  id: "labour-nov2025", title: "4 Labour Codes Effective Nov 2025",
  source: "Labour Ministry", effective_date: "2025-11-21",
  summary: "New labour codes replace 29 existing central labour laws."
})
// ... seed all 5 regulations

// Link regulations to clause types they affect
MATCH (reg1:Regulation {id: "dpdp-may2027"})
MERGE (ct1:ClauseType {type: "data_processing"})
MERGE (ct2:ClauseType {type: "confidentiality"})
MERGE (reg1)-[:AFFECTS_CLAUSE_TYPE]->(ct1)
MERGE (reg1)-[:AFFECTS_CLAUSE_TYPE]->(ct2)
```

**Contracts + Clauses (from PostgreSQL → Neo4j)**
```cypher
// When a contract is uploaded, create graph nodes
CREATE (c:Contract {
  id: $contract_id, title: $title, status: $status,
  contract_type: $contract_type, org_id: $org_id
})
WITH c
UNWIND $clauses as clause
CREATE (cl:Clause {
  id: clause.id, clause_type: clause.clause_type,
  text: clause.text, page_number: clause.page_number
})
MERGE (cl)-[:IN]->(c)
WITH cl, clause
// Link clause to clause type node
MERGE (ct:ClauseType {type: clause.clause_type})
MERGE (cl)-[:HAS_TYPE]->(ct)
```

#### 3. Impact Propagation Queries

**Query: Regulation → Affected Contracts**
```cypher
// Click "DPDP Act" → find all affected contracts
MATCH (reg:Regulation {id: "dpdp-may2027"})-[:AFFECTS_CLAUSE_TYPE]->(ct:ClauseType)
MATCH (ct)<-[:HAS_TYPE]-(cl:Clause)-[:IN]->(c:Contract)
WHERE c.org_id = "demo-org"
RETURN DISTINCT c.id AS contract_id, c.title AS title,
       cl.clause_type AS affected_clause, cl.text AS clause_text
```

**Query: Playbook Rule → Violations**
```cypher
// Click "Max Liability Cap" → find contracts that violate it
MATCH (r:PlaybookRule {id: "rule-1", org_id: "demo-org"})
MATCH (c:Contract {org_id: "demo-org"})-[:HAS_CLAUSE]->(cl:Clause)
WHERE cl.clause_type = r.rule_type
  AND (r.condition = "must_have" OR r.condition = "max_value")
RETURN c.id AS contract_id, c.title AS title,
       cl.text AS clause_text, r.threshold_value AS threshold,
       r.severity AS severity
```

**Query: Statute → Governed Clauses**
```cypher
// Click "Indian Contract Act Section 56" → find all governed clauses
MATCH (s:Statute {id: "ica-s56"})-[:GOVERNS]->(cl:Clause)-[:IN]->(c:Contract)
WHERE c.org_id = "demo-org"
RETURN c.title AS contract, cl.clause_type AS clause_type,
       cl.text AS text, s.enforceability_score AS enforceability
```

### Afternoon: Backend + Frontend (4 hours)

#### 4. Backend Endpoints

```python
# /api/v1/graph/impact/regulation/{reg_id}
# Returns: all contracts affected by a regulation

# /api/v1/graph/impact/playbook/{rule_id}
# Returns: all contracts violating a playbook rule

# /api/v1/graph/impact/statute/{statute_id}
# Returns: all clauses governed by a statute

# /api/v1/graph/rescan-playbook
# Trigger: re-analyze all contracts against current playbook rules
# Returns: new violations found

# /api/v1/graph/contract/{contract_id}/network
# Returns: full subgraph for a contract (clauses, parties, obligations, connected regulations)
```

#### 5. Frontend Graph Visualization

**The 3-Pillar Graph View:**
```
┌─────────────────────────────────────────────────────────────┐
│  3-PILLAR IMPACT GRAPH                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Filter: All Pillars ▼]                                     │
│                                                              │
│     🔵 Playbook          🟢 Law           🔴 Regulatory      │
│                                                              │
│        │                   │                  │              │
│        ▼                   ▼                  ▼              │
│   ┌─────────┐        ┌─────────┐       ┌─────────┐         │
│   │Rule 1   │        │ICA S10  │       │DPDP 2027│         │
│   │Liab Cap │        │         │       │         │         │
│   │₹2Cr max │        │0.95 enf │       │May 2027 │         │
│   └────┬────┘        └────┬────┘       └────┬────┘         │
│        │                  │                 │               │
│        │ VIOLATES         │ GOVERNS         │ AFFECTS       │
│        │                  │                 │               │
│        ▼                  ▼                 ▼               │
│   ┌──────────┐       ┌──────────┐      ┌──────────┐        │
│   │Clause    │       │Clause    │      │Clause    │        │
│   │liability │       │liability │      │data_proc │        │
│   │₹5Cr ❌   │       │clear ✓   │      │missing ❌│        │
│   └────┬─────┘       └────┬─────┘      └────┬─────┘        │
│        │                  │                 │               │
│        └──────────────────┼─────────────────┘               │
│                           │                                 │
│                           ▼                                 │
│                    ┌─────────────┐                          │
│                    │ Contract #5 │                          │
│                    │ Vendor Agmt │                          │
│                    │ Risk: 67 🔴 │                          │
│                    └─────────────┘                          │
│                                                              │
│  [Re-scan Portfolio]  [Export Report]  [Generate Alert]     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Color coding:**
- 🔵 Blue nodes = Playbook rules
- 🟢 Green nodes = Laws/Statutes
- 🔴 Red nodes = Regulations
- ⚪ White nodes = Contracts
- 🟡 Yellow nodes = Clauses

#### 6. "Re-scan Portfolio" Button

When clicked:
1. Backend fetches ALL current playbook rules
2. For each rule, queries all contracts for violations
3. Creates new `[:VIOLATED_BY]` relationships in Neo4j
4. Returns: "Found 3 new violations after playbook update"
5. Frontend: New red edges appear on graph + toast notification

**Demo script:**
> *"We just added a new playbook rule: all vendor contracts need 60-day termination notice. Watch — [clicks Re-scan] — in 2 seconds, REXI found 4 contracts that violate this. Here they are, highlighted in the graph."*

---

## Updated Day 2 Checklist

- [x] Neo4j Docker setup
- [x] **Seed Pillar 1:** Playbook rules as nodes with `[:VIOLATED_BY]` edges
- [x] **Seed Pillar 2:** Statutes as nodes with `[:GOVERNS]` edges
- [x] **Seed Pillar 3:** Regulations as nodes with `[:AFFECTS_CLAUSE_TYPE]` edges
- [x] **Seed contracts + clauses** with `[:IN]` and `[:HAS_TYPE]` edges
- [x] **Impact queries:** Regulation → Contracts, Playbook → Violations, Statute → Clauses
- [x] **`/graph/impact/*` endpoints** for all 3 pillars
- [x] **`/graph/rescan-playbook` endpoint** for auto-detect simulation
- [x] **Frontend graph viz** with color-coded pillar nodes
- [x] **"Re-scan Portfolio" button** with animation
- [x] Redline diff (from original Day 2 plan)

---

## Day 4 Demo Flow: 3-Pillar Moment

```
2:15 — Investor clicks "Knowledge Graph" tab
2:16 — Sees 3 colored legend: 🔵 Playbook  🟢 Law  🔴 Regulatory
2:17 — Investor clicks red node "DPDP Act 2023"
2:18 — Graph animates: red edges spread to ClauseType nodes,
        then to Clause nodes, then to Contract nodes
2:19 — Side panel: "12 contracts affected. 3 have missing data_processing clauses."
2:20 — Investor clicks blue node "Max Liability Cap"
2:21 — Graph shows 4 contracts with VIOLATED_BY edges
2:22 — Side panel: "4 contracts exceed ₹2Cr liability cap"
2:23 — Investor clicks "Re-scan Portfolio" button
2:24 — Spinner → "Found 2 new violations after last playbook update"
2:25 — 2 new red edges animate onto the graph
```

**Investor thinks:** *"This isn't just reading contracts. This is a LIVE legal operating system."*

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/neo4j_service.py` | **NEW** | All Neo4j CRUD + impact queries |
| `backend/app/routers/knowledge_graph.py` | **REPLACE** | 3-pillar impact endpoints |
| `backend/app/core/seed_neo4j.py` | **NEW** | Seeds all 3 pillars on startup |
| `frontend/src/pages/Graph.tsx` | **REPLACE** | 3-pillar interactive graph viz |
| `frontend/src/components/PillarGraph.tsx` | **NEW** | D3.js/vis-network graph with colors |

---

**This is the final, locked plan. Should I start coding Day 1?**
