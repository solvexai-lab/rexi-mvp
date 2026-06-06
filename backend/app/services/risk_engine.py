"""3-layer risk assessment: Playbook (35%) + Law (40%) + Regulatory (25%)."""
import re
from typing import List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.services.knowledge_graph_service import kg_service
from app.models.tables import PlaybookRule, ContractClause, EnforceabilityBenchmark, RegulatoryAlert

class RiskEngine:
    WEIGHTS = {"playbook": 0.35, "law": 0.40, "regulatory": 0.25}

    async def assess(self, contract_id: str, org_id: str, session: AsyncSession) -> Dict:
        pb_findings, pb_score = await self._assess_playbook(contract_id, org_id, session)
        law_findings, law_score = await self._assess_law(contract_id, session)
        reg_findings, reg_score = await self._assess_regulatory(contract_id, org_id, session)
        overall = (pb_score * self.WEIGHTS["playbook"] +
                   law_score * self.WEIGHTS["law"] +
                   reg_score * self.WEIGHTS["regulatory"])
        all_findings = pb_findings + law_findings + reg_findings
        return {
            "overall_score": round(overall, 2),
            "playbook_score": round(pb_score, 2),
            "law_score": round(law_score, 2),
            "regulatory_score": round(reg_score, 2),
            "findings": all_findings
        }

    async def _assess_playbook(self, contract_id: str, org_id: str, session: AsyncSession) -> Tuple[List, float]:
        from app.models.tables import Contract
        # Get contract type
        res_contract = await session.execute(select(Contract).where(Contract.id == contract_id))
        contract = res_contract.scalar_one_or_none()
        contract_type = contract.contract_type if contract else ""

        res_rules = await session.execute(select(PlaybookRule).where(PlaybookRule.org_id == org_id, PlaybookRule.is_active == True))
        all_rules = res_rules.scalars().all()
        # Filter: rule applies if contract_type is empty (universal) or matches contract
        rules = [r for r in all_rules if not r.contract_type or r.contract_type == contract_type]

        res_clauses = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
        clauses = res_clauses.scalars().all()

        findings = []
        for rule in rules:
            relevant = [c for c in clauses if c.clause_type == rule.rule_type]
            if rule.condition == "must_have" and not relevant:
                findings.append({
                    "finding_type": "playbook_violation", "severity": "critical",
                    "title": f"Missing: {rule.rule_name}",
                    "description": f"Contract must include {rule.rule_type} clause",
                    "suggested_amendment": f"Add {rule.rule_type} clause: {rule.threshold_value}",
                    "rule_id": rule.id
                })
            elif rule.condition == "max_value" and relevant:
                for cl in relevant:
                    val = self._extract_number(cl.clause_text)
                    threshold = self._extract_number(rule.threshold_value)
                    if val and threshold and val > threshold:
                        findings.append({
                            "finding_type": "playbook_violation", "severity": "high",
                            "title": f"{rule.rule_name} exceeds limit",
                            "description": f"Value {val} exceeds {threshold}",
                            "suggested_amendment": f"Reduce to {rule.threshold_value}",
                            "rule_id": rule.id, "clause_id": cl.id
                        })
            elif rule.condition == "min_value" and relevant:
                for cl in relevant:
                    val = self._extract_number(cl.clause_text)
                    threshold = self._extract_number(rule.threshold_value)
                    if val and threshold and val < threshold:
                        findings.append({
                            "finding_type": "playbook_violation", "severity": "high",
                            "title": f"{rule.rule_name} below minimum",
                            "description": f"Value {val} is below minimum {threshold}",
                            "suggested_amendment": f"Increase to at least {rule.threshold_value}",
                            "rule_id": rule.id, "clause_id": cl.id
                        })
        score = min(1.0, len(findings) * 0.15)
        return findings, score

    async def _assess_law(self, contract_id: str, session: AsyncSession) -> Tuple[List, float]:
        res_clauses = await session.execute(select(ContractClause).where(ContractClause.contract_id == contract_id))
        clauses = res_clauses.scalars().all()

        res_benchmarks = await session.execute(select(EnforceabilityBenchmark))
        benchmarks = res_benchmarks.scalars().all()

        findings = []
        for cl in clauses:
            matching = [b for b in benchmarks if b.clause_type == cl.clause_type]
            for b in matching:
                if b.enforceability_score < 0.75:
                    findings.append({
                        "finding_type": "law_concern", "severity": "medium",
                        "title": f"Low enforceability: {cl.clause_type}",
                        "description": f"{b.statute_act}, {b.section_number}",
                        "statute_reference": f"{b.statute_act}, {b.section_number}",
                        "suggested_amendment": b.conditions,
                        "clause_id": cl.id
                    })
        score = min(1.0, len(findings) * 0.12)
        return findings, score

    async def _assess_regulatory(self, contract_id: str, org_id: str, session: AsyncSession) -> Tuple[List, float]:
        res_alerts = await session.execute(
            select(RegulatoryAlert).where(
                RegulatoryAlert.org_id == org_id,
                RegulatoryAlert.affected_contract_ids.contains(contract_id)
            )
        )
        alerts = res_alerts.scalars().all()

        findings = []
        for alert in alerts:
            findings.append({
                "finding_type": "regulatory_gap", "severity": "high",
                "title": f"Regulatory: {alert.title}",
                "description": alert.description,
                "suggested_amendment": alert.suggested_actions[0] if alert.suggested_actions else "Review compliance requirements",
            })
        score = min(1.0, len(findings) * 0.18)
        return findings, score

    def _extract_number(self, text: str) -> float:
        nums = re.findall(r'[\d,]+(?:\.\d+)?', text)
        if nums:
            return float(nums[0].replace(",", ""))
        return 0.0

risk_engine = RiskEngine()
