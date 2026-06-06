"""Chunk-aware clause extraction for 400-page contracts.
Pattern from: github.com/neo4j-product-examples/graphrag-contract-review
Processes chunks individually, then merges and deduplicates.
"""
import os
import json
import httpx
from typing import List, Dict
from app.services.chunking_service import chunking_service

class ChunkedClauseExtractor:
    CLAUSE_TYPES = [
        "termination", "liability", "indemnity", "payment", "confidentiality",
        "governing_law", "force_majeure", "non_compete", "intellectual_property",
        "data_processing", "dispute_resolution", "assignment", "amendment", "warranty"
    ]

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self.gpt_model = "gpt-4o-mini"
        self._legal_bert = None
        self._bert_tokenizer = None

    async def extract_from_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Extract clauses from all chunks, then merge and deduplicate."""
        all_clauses = []

        for chunk_data in chunking_service.prepare_for_extraction(chunks):
            text = chunk_data.get("full_context", chunk_data.get("text", ""))
            if len(text) < 50:
                continue

            chunk_clauses = await self._extract_from_text(text)
            for c in chunk_clauses:
                c["chunk_id"] = chunk_data.get("chunk_id")
                c["page_number"] = chunk_data.get("page_number", 1)
                c["heading"] = chunk_data.get("heading", "")
            all_clauses.extend(chunk_clauses)

        # Deduplicate: same clause type + similar text = same clause
        return self._deduplicate_clauses(all_clauses)

    async def _extract_from_text(self, text: str) -> List[Dict]:
        """Extract clauses from a single text segment."""
        if self.openai_key and len(text) > 200:
            return await self._extract_with_gpt(text)
        return self._extract_with_rules(text)

    async def _extract_with_gpt(self, text: str) -> List[Dict]:
        prompt = f"""Extract all contractual clauses from this legal document excerpt. For each clause, provide:
- clause_type: one of [termination, liability, indemnity, payment, confidentiality, governing_law, force_majeure, non_compete, intellectual_property, data_processing, dispute_resolution, assignment, amendment, warranty]
- clause_text: the full clause text (up to 1000 chars)
- confidence: 0.0 to 1.0

Document excerpt:
{text[:5000]}

Return JSON array only."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                    json={"model": self.gpt_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
                    timeout=45
                )
                result = r.json()["choices"][0]["message"]["content"]
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                clauses = json.loads(result)
                for c in clauses:
                    c["page_number"] = c.get("page_number", 1)
                    c["extracted_by"] = "gpt4o_mini"
                    if "confidence" in c:
                        c["confidence_score"] = float(c.pop("confidence"))
                return clauses
        except Exception:
            return self._extract_with_rules(text)

    def _extract_with_rules(self, text: str) -> List[Dict]:
        """Rule-based extraction with legal numbering awareness."""
        paragraphs = []
        # Split by legal numbering patterns (1.1, (a), etc.)
        import re
        # First try splitting by numbered clauses
        parts = re.split(r'\n(?=\d+\.\d+\s|\([a-zA-Z]\)\s|^Article\s+\d+)', text)
        if len(parts) < 3:
            parts = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]

        for p in parts:
            p = p.strip()
            if len(p) > 30 and len(p) < 2000:
                paragraphs.append(p)

        clauses = []
        for p in paragraphs:
            p_lower = p.lower()
            for clause_type in self.CLAUSE_TYPES:
                keywords = clause_type.replace("_", " ").split()
                if any(kw in p_lower for kw in keywords):
                    clauses.append({
                        "clause_type": clause_type,
                        "clause_text": p[:1500],
                        "page_number": 1,
                        "confidence_score": 0.7,
                        "extracted_by": "rule_based"
                    })
                    break
        return clauses

    def _deduplicate_clauses(self, clauses: List[Dict]) -> List[Dict]:
        """Remove duplicate clauses based on type + text similarity."""
        unique = []
        seen_texts = []

        for c in clauses:
            ct = c.get("clause_type", "")
            text = c.get("clause_text", "")[:100].lower()
            is_dup = False

            for seen in seen_texts:
                if seen["type"] == ct and self._text_similarity(seen["text"], text) > 0.7:
                    is_dup = True
                    break

            if not is_dup:
                seen_texts.append({"type": ct, "text": text})
                unique.append(c)

        return unique

    def _text_similarity(self, a: str, b: str) -> float:
        """Simple Jaccard similarity for deduplication."""
        set_a = set(a.split())
        set_b = set(b.split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    async def extract_entities_from_chunks(self, chunks: List[Dict]) -> Dict:
        """Extract contract-level entities using progressive context."""
        # Use first few chunks for entity extraction (usually front matter)
        front_text = "\n".join(c.get("text", "") for c in chunks[:5])
        if self.openai_key and len(front_text) > 100:
            return await self._extract_entities_with_gpt(front_text)
        return {}

    async def _extract_entities_with_gpt(self, text: str) -> Dict:
        prompt = f"""Extract from this contract: parties (name, role), start_date, end_date, auto_renewal (boolean), governing_law, value_inr (number), jurisdiction. Document: {text[:5000]}. Return JSON only."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                    json={"model": self.gpt_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
                    timeout=30
                )
                result = r.json()["choices"][0]["message"]["content"]
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                return json.loads(result)
        except Exception:
            return {}

    async def extract_obligations_from_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Extract obligations from all chunks."""
        all_obligations = []
        for chunk in chunks:
            text = chunk.get("text", "")
            if len(text) < 100:
                continue
            obs = await self._extract_obligations_with_gpt(text)
            for o in obs:
                o["chunk_id"] = chunk.get("chunk_id")
            all_obligations.extend(obs)
        return self._deduplicate_obligations(all_obligations)

    async def _extract_obligations_with_gpt(self, text: str) -> List[Dict]:
        if not self.openai_key:
            return []
        prompt = f"""Extract obligations from this contract section. Each: description, type (payment/delivery/reporting/compliance/renewal), responsible_party, due_date (YYYY-MM-DD or null). Section: {text[:3000]}. Return JSON array only."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                    json={"model": self.gpt_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
                    timeout=30
                )
                result = r.json()["choices"][0]["message"]["content"]
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                return json.loads(result)
        except Exception:
            return []

    def _deduplicate_obligations(self, obligations: List[Dict]) -> List[Dict]:
        """Deduplicate obligations by description similarity."""
        unique = []
        seen = set()
        for o in obligations:
            desc = o.get("description", "").lower()[:80]
            if desc and desc not in seen:
                seen.add(desc)
                unique.append(o)
        return unique

chunked_clause_extractor = ChunkedClauseExtractor()
