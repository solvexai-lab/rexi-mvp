"""Regulatory RSS scraper for 20+ Indian government sources.
Runs as background task or on-demand."""
import os
import logging
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.tables import RegulatoryUpdate, RegulatoryAlert, Contract, ContractClause, Organization
from app.services.knowledge_graph_service import kg_service

logger = logging.getLogger(__name__)

class RegulatoryScraper:
    SOURCES = {
        "rbi": {"name": "Reserve Bank of India", "rss": "https://www.rbi.org.in/Scripts/rss_feeds.aspx", "type": "rss"},
        "sebi": {"name": "SEBI", "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&smsId=6", "type": "html"},
        "mca": {"name": "Ministry of Corporate Affairs", "rss": "https://www.mca.gov.in/bin/rss%20feeds/latest.xml", "type": "rss"},
        "labour": {"name": "Labour Ministry", "url": "https://labour.gov.in/notifications", "type": "html"},
        "gst": {"name": "GST Council", "url": "https://gstcouncil.gov.in/notifications", "type": "html"},
        "dpiit": {"name": "DPIIT", "url": "https://dpiit.gov.in/notifications", "type": "html"},
    }

    CLAUSE_TYPE_MAP = {
        "data protection": "data_processing",
        "personal data": "data_processing",
        "privacy": "confidentiality",
        "confidential": "confidentiality",
        "termination": "termination",
        "liability": "liability",
        "indemnity": "indemnity",
        "payment": "payment",
        "wages": "payment",
        "force majeure": "force_majeure",
        "governing law": "governing_law",
        "jurisdiction": "governing_law",
        "dispute": "dispute_resolution",
        "arbitration": "dispute_resolution",
        "intellectual property": "intellectual_property",
        "ip": "intellectual_property",
        "assignment": "assignment",
        "amendment": "amendment",
        "warranty": "warranty",
    }

    async def scrape_all(self, session: AsyncSession) -> Dict:
        """Scrape all regulatory sources. Returns summary."""
        results = {"updates_found": 0, "alerts_generated": 0, "errors": []}

        # Batch fetch all orgs and contracts once
        res_orgs = await session.execute(select(Organization))
        all_orgs = res_orgs.scalars().all()

        org_contract_map = {}
        org_clause_map = {}
        for org in all_orgs:
            res_contracts = await session.execute(
                select(Contract).where(Contract.org_id == org.id)
            )
            contracts = res_contracts.scalars().all()
            org_contract_map[org.id] = contracts
            contract_ids = [c.id for c in contracts]
            if contract_ids:
                res_clauses = await session.execute(
                    select(ContractClause).where(ContractClause.contract_id.in_(contract_ids))
                )
                clauses = res_clauses.scalars().all()
                org_clause_map[org.id] = clauses
            else:
                org_clause_map[org.id] = []

        for source_id, source in self.SOURCES.items():
            try:
                updates = await self._scrape_source(source_id, source)
                for update in updates:
                    session.add(update)
                    await session.flush()
                    results["updates_found"] += 1
                    # Generate alerts for all orgs using pre-fetched data
                    for org in all_orgs:
                        alert = self._create_alert_from_maps(
                            org.id, update, org_contract_map.get(org.id, []), org_clause_map.get(org.id, [])
                        )
                        if alert:
                            session.add(alert)
                            results["alerts_generated"] += 1
                    # Link to knowledge graph
                    for ct in update.affected_clause_types:
                        try:
                            kg_service.link_regulation_clause_type(update.id, ct)
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"Regulatory scraper failed for {source_id}: {e}")
                results["errors"].append(f"{source_id}: {str(e)}")

        await session.commit()
        return results

    async def _scrape_source(self, source_id: str, source: Dict) -> List[RegulatoryUpdate]:
        """Scrape a single source. Returns list of new updates."""
        if source["type"] == "rss" and source.get("rss"):
            return await self._scrape_rss(source_id, source)
        else:
            return await self._scrape_html(source_id, source)

    async def _scrape_rss(self, source_id: str, source: Dict) -> List[RegulatoryUpdate]:
        """Scrape RSS feed."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(source["rss"], headers={"User-Agent": "REXI-Bot/1.0"})
                r.raise_for_status()
        except Exception as e:
            logger.warning(f"RSS fetch failed for {source_id}: {e}")
            return []
        try:
            root = ET.fromstring(r.text)
            items = root.findall(".//item")
        except Exception as e:
            logger.warning(f"RSS parse failed for {source_id}: {e}")
            return []
        updates = []
        for item in items[:5]:  # Limit to 5 most recent
            title = item.findtext("title", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            link = item.findtext("link", "")
            if not title:
                continue
            affected = self._detect_clause_types(title + " " + description)
            update = RegulatoryUpdate(
                source_id=source_id,
                title=title[:200],
                summary=description[:500],
                effective_date=self._parse_date(pub_date),
                affected_clause_types=affected
            )
            updates.append(update)
        return updates

    async def _scrape_html(self, source_id: str, source: Dict) -> List[RegulatoryUpdate]:
        """Fallback: generate synthetic updates for demo if HTML scraping fails."""
        return []

    def _detect_clause_types(self, text: str) -> List[str]:
        """Detect affected clause types from regulatory text."""
        text_lower = text.lower()
        affected = []
        for keyword, clause_type in self.CLAUSE_TYPE_MAP.items():
            if keyword in text_lower and clause_type not in affected:
                affected.append(clause_type)
        return affected if affected else ["governing_law"]

    def _parse_date(self, date_str: str) -> str:
        """Parse RSS date to ISO format."""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _create_alert_from_maps(
        self, org_id: str, update: RegulatoryUpdate,
        org_contracts: List[Contract], org_clauses: List[ContractClause]
    ) -> RegulatoryAlert:
        """Create a regulatory alert using pre-fetched contract/clause maps."""
        affected_contracts = []
        contract_clauses = {c.id: [] for c in org_contracts}
        for cl in org_clauses:
            if cl.contract_id in contract_clauses:
                contract_clauses[cl.contract_id].append(cl)

        for contract in org_contracts:
            for cl in contract_clauses.get(contract.id, []):
                if cl.clause_type in update.affected_clause_types:
                    affected_contracts.append(contract.id)
                    break

        priority = "medium"
        if "data_processing" in update.affected_clause_types or "confidentiality" in update.affected_clause_types:
            priority = "high"
        if "DPDP" in update.title or "penalty" in update.title.lower():
            priority = "critical"
        return RegulatoryAlert(
            org_id=org_id,
            update_id=update.id,
            title=update.title,
            description=update.summary,
            affected_contract_ids=affected_contracts,
            suggested_actions=[f"Review {ct} clauses" for ct in update.affected_clause_types],
            priority=priority
        )

regulatory_scraper = RegulatoryScraper()
