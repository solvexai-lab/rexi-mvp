"""Tamper-proof audit trail with cryptographic chaining.
Each entry includes a SHA-256 hash of its content + the previous entry's hash,
creating a blockchain-like chain of custody."""
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.tables import AuditTrailEntry

class AuditService:
    """Append-only audit log with Merkle-style chaining."""

    def _hash_entry(self, entry_data: Dict[str, Any], previous_hash: str) -> str:
        """Compute SHA-256 hash of entry content + previous hash."""
        data = {
            "org_id": entry_data.get("org_id", ""),
            "actor_id": entry_data.get("actor_id", ""),
            "action": entry_data.get("action", ""),
            "resource_type": entry_data.get("resource_type", ""),
            "resource_id": entry_data.get("resource_id", ""),
            "details": entry_data.get("details", {}),
            "previous_hash": previous_hash,
            "timestamp": entry_data.get("created_at", datetime.utcnow().isoformat()),
        }
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def log_action(
        self,
        session: AsyncSession,
        org_id: str,
        actor_id: str,
        actor_email: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditTrailEntry:
        """Log an action with cryptographic chaining."""
        # Get previous entry hash for this org
        result = await session.execute(
            select(AuditTrailEntry)
            .where(AuditTrailEntry.org_id == org_id)
            .order_by(AuditTrailEntry.created_at.desc())
        )
        previous = result.scalars().first()
        previous_hash = previous.entry_hash if previous else "0" * 64

        # Use single timestamp for both hash and DB
        now = datetime.utcnow()
        entry_data = {
            "org_id": org_id,
            "actor_id": actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "created_at": now.isoformat(),
        }
        entry_hash = self._hash_entry(entry_data, previous_hash)

        entry = AuditTrailEntry(
            org_id=org_id,
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            created_at=now,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry

    async def verify_chain(self, session: AsyncSession, org_id: str) -> Dict[str, Any]:
        """Verify the integrity of the audit chain for an org.
        Returns: {valid: bool, entries_checked: int, first_broken_id: str|None}"""
        result = await session.execute(
            select(AuditTrailEntry)
            .where(AuditTrailEntry.org_id == org_id)
            .order_by(AuditTrailEntry.created_at)
        )
        entries = result.scalars().all()

        if not entries:
            return {"valid": True, "entries_checked": 0, "first_broken_id": None}

        previous_hash = "0" * 64
        for entry in entries:
            entry_data = {
                "org_id": entry.org_id,
                "actor_id": entry.actor_id,
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "details": entry.details,
                "created_at": entry.created_at.isoformat() if entry.created_at else "",
            }
            computed_hash = self._hash_entry(entry_data, previous_hash)
            if computed_hash != entry.entry_hash:
                return {"valid": False, "entries_checked": len(entries), "first_broken_id": entry.id}
            previous_hash = entry.entry_hash

        return {"valid": True, "entries_checked": len(entries), "first_broken_id": None}

    async def get_trail(
        self,
        session: AsyncSession,
        org_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """Get audit trail entries for an org, optionally filtered."""
        query = select(AuditTrailEntry).where(AuditTrailEntry.org_id == org_id)
        if resource_type:
            query = query.where(AuditTrailEntry.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditTrailEntry.resource_id == resource_id)
        query = query.order_by(AuditTrailEntry.created_at.desc()).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()


audit_service = AuditService()
