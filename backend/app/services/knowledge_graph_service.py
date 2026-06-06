"""Neo4j Knowledge Graph — Optional. Falls back gracefully if Neo4j is unavailable.
Integrates literal graphrag-contract Cypher schema alongside legacy REXI schema.
"""
import os
from typing import List, Dict, Optional

from app.services.graphrag_cypher import (
    CREATE_GRAPH_STATEMENT,
    CREATE_VECTOR_INDEX_STATEMENT,
    CREATE_FULL_TEXT_INDICES,
    EMBEDDINGS_STATEMENT,
    NEO4J_SCHEMA,
    ContractSearchService,
    create_full_text_indices,
)


class KnowledgeGraphService:
    def __init__(self):
        self._available = False
        self.driver = None
        self.search_service: Optional[ContractSearchService] = None
        try:
            from neo4j import GraphDatabase
            uri = os.getenv("NEO4J_URI", "")
            if not uri:
                return
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "rexi_neo4j_2025")
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Quick connectivity test
            self.driver.verify_connectivity()
            self._available = True
            self.search_service = ContractSearchService(self.driver)
        except Exception:
            self._available = False
            self.driver = None

    # ──────────────────────────── Low-level execute ────────────────────────────
    def _execute(self, query: str, **params):
        if not self._available or not self.driver:
            return []
        try:
            with self.driver.session() as session:
                return session.run(query, **params).data()
        except Exception:
            return []

    # ──────────────────────────── Legacy REXI schema CRUD ────────────────────────────

    def create_contract_node(self, contract_id: str, title: str, contract_type: str,
                             status: str, governing_law: str, value_inr: float) -> None:
        self._execute("""
            MERGE (c:Contract {id: $id})
            SET c.title = $title, c.contract_type = $type, c.status = $status,
                c.governing_law = $law, c.value_inr = $value
        """, id=contract_id, title=title, type=contract_type, status=status, law=governing_law, value=value_inr)

    def create_party_node(self, party_id: str, name: str, email: str = "", party_type: str = "vendor") -> None:
        self._execute("""
            MERGE (p:Party {id: $id})
            SET p.name = $name, p.email = $email, p.party_type = $ptype
        """, id=party_id, name=name, email=email, ptype=party_type)

    def create_clause_node(self, clause_id: str, clause_type: str, clause_text: str,
                           page_number: int, confidence: float) -> None:
        self._execute("""
            MERGE (cl:Clause {id: $id})
            SET cl.clause_type = $ctype, cl.text = $text,
                cl.page_number = $page, cl.confidence = $conf
        """, id=clause_id, ctype=clause_type, text=clause_text[:500], page=page_number, conf=confidence)

    def create_statute_node(self, statute_id: str, act_name: str, section: str,
                            section_text: str, enforceability: float) -> None:
        self._execute("""
            MERGE (s:Statute {id: $id})
            SET s.act_name = $act, s.section = $section,
                s.section_text = $text, s.enforceability = $score
        """, id=statute_id, act=act_name, section=section, text=section_text[:500], score=enforceability)

    def create_regulation_node(self, reg_id: str, title: str, source: str,
                               effective_date: str, summary: str = "") -> None:
        self._execute("""
            MERGE (r:Regulation {id: $id})
            SET r.title = $title, r.source = $source,
                r.effective_date = $date, r.summary = $summary
        """, id=reg_id, title=title, source=source, date=effective_date, summary=summary[:500])

    def create_obligation_node(self, ob_id: str, description: str, ob_type: str,
                               due_date: str, status: str = "pending") -> None:
        self._execute("""
            MERGE (o:Obligation {id: $id})
            SET o.description = $desc, o.obligation_type = $otype,
                o.due_date = $date, o.status = $status
        """, id=ob_id, desc=description[:500], otype=ob_type, date=due_date, status=status)

    def link_org_contract(self, org_id: str, contract_id: str):
        self._execute("""
            MERGE (o:Organization {id: $oid})
            MERGE (c:Contract {id: $cid})
            MERGE (o)-[:HAS_CONTRACT]->(c)
        """, oid=org_id, cid=contract_id)

    def link_contract_party(self, contract_id: str, party_id: str, role: str = "counterparty"):
        self._execute("""
            MATCH (c:Contract {id: $cid}), (p:Party {id: $pid})
            MERGE (c)-[:HAS_PARTY {role: $role}]->(p)
        """, cid=contract_id, pid=party_id, role=role)

    def link_contract_clause(self, contract_id: str, clause_id: str):
        self._execute("""
            MATCH (c:Contract {id: $cid}), (cl:Clause {id: $clid})
            MERGE (c)-[:HAS_CLAUSE]->(cl)
        """, cid=contract_id, clid=clause_id)

    def link_clause_statute(self, clause_id: str, statute_id: str):
        self._execute("""
            MATCH (cl:Clause {id: $clid}), (s:Statute {id: $sid})
            MERGE (cl)-[:GOVERNED_BY]->(s)
        """, clid=clause_id, sid=statute_id)

    def link_contract_obligation(self, contract_id: str, ob_id: str):
        self._execute("""
            MATCH (c:Contract {id: $cid}), (o:Obligation {id: $oid})
            MERGE (c)-[:HAS_OBLIGATION]->(o)
        """, cid=contract_id, oid=ob_id)

    def link_regulation_clause_type(self, reg_id: str, clause_type: str):
        self._execute("""
            MATCH (r:Regulation {id: $rid})
            MERGE (ct:ClauseType {type: $ctype})
            MERGE (r)-[:AFFECTS_CLAUSE_TYPE]->(ct)
        """, rid=reg_id, ctype=clause_type)

    def get_regulation_impact(self, regulation_id: str) -> List[Dict]:
        return self._execute("""
            MATCH (r:Regulation {id: $rid})-[:AFFECTS_CLAUSE_TYPE]->(ct:ClauseType)
            MATCH (cl:Clause {clause_type: ct.type})<-[:HAS_CLAUSE]-(c:Contract)
            MATCH (o:Organization)-[:HAS_CONTRACT]->(c)
            RETURN o.id as org_id, o.name as org_name, c.id as contract_id,
                   c.title as title, collect(DISTINCT cl.clause_type) as affected_clauses
        """, rid=regulation_id)

    def get_contract_network(self, contract_id: str) -> List[Dict]:
        return self._execute("""
            MATCH (c:Contract {id: $id})
            MATCH path = (c)-[*1..3]-(related)
            WITH nodes(path) as ns, relationships(path) as rels
            RETURN [n in ns | {id: n.id, label: labels(n)[0], name: coalesce(n.title, n.name, n.clause_type, "")}] as nodes,
                   [r in rels | {type: type(r), source: startNode(r).id, target: endNode(r).id}] as rels
            LIMIT 100
        """, id=contract_id)

    def get_org_contracts_summary(self, org_id: str) -> List[Dict]:
        return self._execute("""
            MATCH (o:Organization {id: $oid})-[:HAS_CONTRACT]->(c:Contract)
            OPTIONAL MATCH (c)-[:HAS_CLAUSE]->(cl:Clause)
            RETURN c.id as id, c.title as title, c.status as status,
                   c.contract_type as type, count(cl) as clause_count
            ORDER BY c.title
        """, oid=org_id)

    def seed_statutes(self):
        statutes = [
            ("ica_s10", "Indian Contract Act, 1872", "Section 10", "What agreements are contracts.", 0.95),
            ("ica_s56", "Indian Contract Act, 1872", "Section 56", "Agreement to do impossible act is void.", 0.90),
            ("ica_s73", "Indian Contract Act, 1872", "Section 73", "Compensation for loss or damage.", 0.88),
            ("sra_s10", "Specific Relief Act, 1963", "Section 10", "Cases in which specific performance enforceable.", 0.85),
            ("dpdp_2023", "DPDP Act, 2023", "Section 12", "Consent requirement for data processing.", 0.92),
            ("dpdp_2023_p", "DPDP Act, 2023", "Penalty Section", "Up to 250 Cr for data breach.", 0.95),
            ("cpca_2019", "Consumer Protection Act, 2019", "Section 2", "Definition of consumer rights.", 0.87),
            ("ca_2013", "Companies Act, 2013", "Section 134", "Financial statement, Board's report.", 0.90),
            ("rbi_2024", "RBI Act, 1934", "Circular 2024-01", "NPA classification norms.", 0.82),
            ("sebi_lodr", "SEBI LODR, 2015", "Regulation 27", "Corporate governance compliance.", 0.88),
        ]
        for s in statutes:
            self.create_statute_node(*s)

    def seed_regulations(self):
        regs = [
            ("dpdp_may2027", "DPDP Compliance Deadline May 2027", "DPDP Board", "2027-05-13", "All data fiduciaries must comply by May 2027. Penalty up to 250 Cr."),
            ("labour_nov2025", "4 Labour Codes Effective Nov 2025", "Labour Ministry", "2025-11-21", "New labour codes replace 29 existing laws."),
            ("mca_v3", "MCA V3 Portal Migration", "MCA", "2025-07-14", "38 e-forms migrated to new portal."),
            ("rbi_npa", "RBI NPA Classification Changes", "RBI", "2025-04-01", "Changed NPA recognition norms for banks."),
            ("sebi_lodr_2025", "SEBI LODR Disclosure Amendments", "SEBI", "2025-06-01", "Enhanced corporate governance disclosures."),
        ]
        for r in regs:
            self.create_regulation_node(*r)
            if r[0] == "dpdp_may2027":
                self.link_regulation_clause_type(r[0], "data_processing")
                self.link_regulation_clause_type(r[0], "confidentiality")
            elif r[0] == "labour_nov2025":
                self.link_regulation_clause_type(r[0], "termination")
                self.link_regulation_clause_type(r[0], "payment")

    # ──────────────────────────── GraphRAG schema integration ────────────────────────────

    def create_graphrag_contract(
        self,
        agreement_id: str,
        agreement_name: str,
        language: str = "en",
        effective_date: str = "2024-01-01",
        initial_term: str = "12 months",
        renewal_term: str = "12 months",
        inception_date: str = "2024-01-01",
        status: str = "active",
        country_name: str = "India",
        governing_law_country: str = "India",
        organization_name: str = "Demo Org",
        organization_id: str = "demo-org",
        organization_address: str = "",
        organization_role: str = "signatory",
        clauses: Optional[List[Dict]] = None,
    ) -> bool:
        """Create a contract using the literal graphrag-contract Cypher schema.
        Falls back gracefully if Neo4j unavailable.
        """
        if not self._available or not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run(
                    CREATE_GRAPH_STATEMENT,
                    agreement_id=agreement_id,
                    agreement_name=agreement_name,
                    agreement_language=language,
                    agreement_effective_date=effective_date,
                    agreement_initial_term=initial_term,
                    agreement_renewal_term=renewal_term,
                    agreement_inception_date=inception_date,
                    agreement_status=status,
                    country_name=country_name,
                    governing_law_country_name=governing_law_country,
                    organization_name=organization_name,
                    organization_id=organization_id,
                    organization_address=organization_address,
                    organization_role=organization_role,
                    clauses=clauses or [],
                )
            return True
        except Exception:
            return False

    def ensure_graphrag_indices(self) -> bool:
        """Create vector + fulltext indexes per graphrag-contract schema."""
        if not self._available or not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run(CREATE_VECTOR_INDEX_STATEMENT)
            create_full_text_indices(self.driver)
            return True
        except Exception:
            return False

    def compute_graphrag_embeddings(self) -> int:
        """Generate embeddings for Excerpt nodes. Requires OPENAI_API_KEY."""
        if not self._available or not self.driver:
            return 0
        try:
            token = os.getenv("OPENAI_API_KEY", "")
            if not token:
                return 0
            with self.driver.session() as session:
                result = session.run(EMBEDDINGS_STATEMENT, {"openai_token": token})
                record = result.single()
                return record["embedded_count"] if record else 0
        except Exception:
            return 0

    def get_graphrag_contract(self, contract_id: str) -> Optional[Dict]:
        """Get contract using graphrag-contract search service."""
        if self.search_service:
            return self.search_service.get_contract(contract_id)
        return None


kg_service = KnowledgeGraphService()
