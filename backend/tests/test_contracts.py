"""Contract CRUD tests."""
import pytest

@pytest.mark.asyncio
async def test_list_contracts(client):
    resp = await client.get("/api/v1/contracts?org_id=demo-org")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_and_get_contract(client, db_session):
    from app.models.tables import Contract
    # Create via DB directly for simplicity
    c = Contract(org_id="demo-org", title="Test Contract", status="draft")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    resp = await client.get(f"/api/v1/contracts/{c.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract"]["title"] == "Test Contract"

@pytest.mark.asyncio
async def test_contract_not_found(client):
    resp = await client.get("/api/v1/contracts/nonexistent-id")
    assert resp.status_code == 404
