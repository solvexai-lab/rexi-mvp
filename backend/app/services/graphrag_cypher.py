"""Literal copy-paste from graphrag-contract/create_graph_from_json.py + ContractService.py.
Cypher schema for Neo4j GraphRAG contract analysis.
"""
from typing import Optional
import os

# ────────────────────────── Cypher statements (verbatim) ──────────────────────────

CREATE_GRAPH_STATEMENT = """
MERGE (agreement:Agreement {id: $agreement_id})
SET agreement.name = $agreement_name,
    agreement.language = $agreement_language,
    agreement.effectiveDate = date($agreement_effective_date),
    agreement.initialTerm = $agreement_initial_term,
    agreement.renewalTerm = $agreement_renewal_term,
    agreement.inceptionDate = $agreement_inception_date,
    agreement.status = $agreement_status

MERGE (country:Country {name: $country_name})

MERGE (governingLaw:Country {name: $governing_law_country_name})

MERGE (organization:Organization {name: $organization_name})
SET organization.id = $organization_id,
    organization.address = $organization_address,
    organization.role = $organization_role

MERGE (agreement)-[:GOVERNED_BY]->(governingLaw)
MERGE (organization)-[:SIGNED]->(agreement)
MERGE (agreement)-[:HAS_COUNTRY]->(country)

WITH agreement, country, governingLaw, organization
UNWIND $clauses as clause
MERGE (c:ContractClause {id: clause.id})
SET c.name = clause.name

MERGE (agreement)-[:HAS_CLAUSE {page: clause.page}]->(c)

MERGE (type:ClauseType {name: clause.type})
MERGE (c)-[:HAS_TYPE]->(type)

WITH agreement, c, clause, country
UNWIND clause.excerpts as excerpt
MERGE (e:Excerpt {id: excerpt.id})
SET e.text = excerpt.text

MERGE (c)-[:HAS_EXCERPT {order: excerpt.order}]->(e)
MERGE (e)-[:HAS_COUNTRY]->(country)
"""

CREATE_VECTOR_INDEX_STATEMENT = """
CREATE VECTOR INDEX agreementVector IF NOT EXISTS
FOR (e:Excerpt) ON (e.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}}"""

CREATE_FULL_TEXT_INDICES = """
CREATE FULLTEXT INDEX agreementTextIndex IF NOT EXISTS
FOR (a:Agreement) ON EACH [a.name];

CREATE FULLTEXT INDEX excerptTextIndex IF NOT EXISTS
FOR (e:Excerpt) ON EACH [e.text];

CREATE FULLTEXT INDEX clauseTypeTextIndex IF NOT EXISTS
FOR (t:ClauseType) ON EACH [t.name];

CREATE FULLTEXT INDEX clauseTextIndex IF NOT EXISTS
FOR (c:ContractClause) ON EACH [c.name];

CREATE FULLTEXT INDEX organizationNameTextIndex IF NOT EXISTS
FOR (o:Organization) ON EACH [o.name];

CREATE FULLTEXT INDEX organizationAddressTextIndex IF NOT EXISTS
FOR (o:Organization) ON EACH [o.address];"""

EMBEDDINGS_STATEMENT = """
MATCH (e:Excerpt)
WHERE e.embedding IS NULL
WITH e, genai.vector.encode(e.text, "OpenAI", {token: $openai_token}) AS embedding
CALL db.create.setNodeVectorProperty(e, "embedding", embedding)
RETURN count(*) as embedded_count"""

GET_CONTRACT_BY_ID_QUERY = """
MATCH (agreement:Agreement {id: $id})-[:HAS_CLAUSE]->(clause:ContractClause)
MATCH (clause)-[:HAS_TYPE]->(type:ClauseType)
OPTIONAL MATCH (clause)-[:HAS_EXCERPT]->(excerpt:Excerpt)
WITH agreement, clause, type, collect({text: excerpt.text, order: excerpt.order}) AS excerpts
RETURN agreement.id as id,
       agreement.name as name,
       collect({clause: clause.name, type: type.name, excerpts: excerpts}) AS clauses
"""

NEO4J_SCHEMA = """
Node properties:
- Agreement {id: STRING, name: STRING, language: STRING, effectiveDate: DATE, initialTerm: STRING, renewalTerm: STRING, inceptionDate: DATE, status: STRING}
- Country {name: STRING}
- Organization {id: STRING, name: STRING, address: STRING, role: STRING}
- ContractClause {id: STRING, name: STRING}
- ClauseType {name: STRING}
- Excerpt {id: STRING, text: STRING, embedding: LIST<FLOAT>}

Relationship properties:
- HAS_CLAUSE {page: INTEGER}
- HAS_EXCERPT {order: INTEGER}

The relationships:
(:Agreement)-[:GOVERNED_BY]->(:Country)
(:Organization)-[:SIGNED]->(:Agreement)
(:Agreement)-[:HAS_COUNTRY]->(:Country)
(:Agreement)-[:HAS_CLAUSE]->(:ContractClause)
(:ContractClause)-[:HAS_TYPE]->(:ClauseType)
(:ContractClause)-[:HAS_EXCERPT]->(:Excerpt)
(:Excerpt)-[:HAS_COUNTRY]->(:Country)
"""


def create_full_text_indices(driver) -> None:
    """Run the fulltext index creation statements."""
    for statement in CREATE_FULL_TEXT_INDICES.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            driver.execute_query(stmt)


# ────────────────────────── ContractSearchService (verbatim) ──────────────────────────

class ContractSearchService:
    """Literal adaptation of graphrag-contract ContractService.py."""

    def __init__(self, driver, openai_api_key: Optional[str] = None):
        self.driver = driver
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY", "")

    def get_contract(self, contract_id: str):
        with self.driver.session() as session:
            result = session.run(GET_CONTRACT_BY_ID_QUERY, {"id": contract_id})
            record = result.single()
            if record is None:
                return None
            return {
                "id": record["id"],
                "name": record["name"],
                "clauses": record["clauses"],
            }

    def get_contracts(self, organization_name: str):
        query = """
        CALL db.index.fulltext.queryNodes('organizationNameTextIndex', $name)
        YIELD node, score
        MATCH (node)-[:SIGNED]->(agreement:Agreement)
        RETURN agreement.id as id, agreement.name as name, score
        """
        with self.driver.session() as session:
            result = session.run(query, {"name": organization_name})
            return [{"id": r["id"], "name": r["name"], "score": r["score"]} for r in result]

    def get_contracts_with_clause_type(self, clause_type: str):
        query = """
        CALL db.index.fulltext.queryNodes('clauseTypeTextIndex', $type)
        YIELD node, score
        MATCH (node)<-[:HAS_TYPE]-(clause:ContractClause)<-[:HAS_CLAUSE]-(agreement:Agreement)
        RETURN DISTINCT agreement.id as id, agreement.name as name, score
        """
        with self.driver.session() as session:
            result = session.run(query, {"type": clause_type})
            return [{"id": r["id"], "name": r["name"], "score": r["score"]} for r in result]

    def get_contracts_without_clause(self, clause_type: str):
        query = """
        MATCH (agreement:Agreement)
        WHERE NOT (agreement)-[:HAS_CLAUSE]->(:ContractClause)-[:HAS_TYPE]->(:ClauseType {name: $type})
        RETURN agreement.id as id, agreement.name as name
        """
        with self.driver.session() as session:
            result = session.run(query, {"type": clause_type})
            return [{"id": r["id"], "name": r["name"]} for r in result]

    def get_contracts_similar_text(self, clause_text: str, top_k: int = 3):
        """Vector similarity search on Excerpt embeddings.
        Requires Neo4j 5.15+ with vector index + OpenAI embedding call.
        Falls back gracefully if vector index missing.
        """
        if not self.openai_api_key:
            return []
        try:
            query = """
            CALL db.index.vector.queryNodes('agreementVector', $top_k,
                genai.vector.encode($text, "OpenAI", {token: $token})
            )
            YIELD node AS excerpt, score
            MATCH (excerpt)<-[:HAS_EXCERPT]-(clause:ContractClause)<-[:HAS_CLAUSE]-(agreement:Agreement)
            RETURN agreement.id as id, agreement.name as name, score, excerpt.text as matched_text
            """
            with self.driver.session() as session:
                result = session.run(query, {
                    "top_k": top_k, "text": clause_text,
                    "token": self.openai_api_key
                })
                return [
                    {"id": r["id"], "name": r["name"],
                     "score": r["score"], "matched_text": r["matched_text"]}
                    for r in result
                ]
        except Exception:
            return []

    def answer_aggregation_question(self, user_question: str):
        """Text2Cypher: convert natural language to Cypher and run.
        Requires OpenAI API for LLM-based Text2Cypher.
        """
        # Simplified implementation — in production, call an LLM to generate Cypher
        # from NEO4J_SCHEMA + user_question.
        return {"answer": "Text2Cypher requires LLM integration.", "cypher": ""}
