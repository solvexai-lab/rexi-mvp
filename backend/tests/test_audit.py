"""Audit trail integrity tests."""
import pytest
from app.services.audit_service import audit_service

@pytest.mark.asyncio
async def test_audit_log_and_verify(client, db_session):
    entry = await audit_service.log_action(
        session=db_session,
        org_id="demo-org",
        actor_id="user-1",
        actor_email="user@rexi.ai",
        action="contract_created",
        resource_type="contract",
        resource_id="contract-123",
        details={"title": "Test Contract"}
    )
    assert entry.id is not None
    assert entry.entry_hash is not None
    assert entry.previous_hash is not None

    # Verify chain
    result = await audit_service.verify_chain(db_session, "demo-org")
    assert result["valid"] is True
    assert result["entries_checked"] == 1

@pytest.mark.asyncio
async def test_audit_chain_multiple_entries(client, db_session):
    for i in range(3):
        await audit_service.log_action(
            session=db_session,
            org_id="demo-org",
            actor_id="user-1",
            actor_email="user@rexi.ai",
            action=f"action_{i}",
            resource_type="contract",
            resource_id=f"contract-{i}",
            details={"index": i}
        )
    result = await audit_service.verify_chain(db_session, "demo-org")
    assert result["valid"] is True
    assert result["entries_checked"] == 3

@pytest.mark.asyncio
async def test_audit_trail_api(client):
    resp = await client.get("/api/v1/audit/trail?org_id=demo-org")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_audit_verify_api(client):
    resp = await client.post("/api/v1/audit/trail/verify?org_id=demo-org")
    assert resp.status_code == 200
    data = resp.json()
    assert "valid" in data
