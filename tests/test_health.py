import pytest


@pytest.mark.asyncio
async def test_health_endpoints(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

    r = await client.get("/api/v1/health/ready")
    assert r.status_code == 200

    r = await client.get("/api/v1/health/live")
    assert r.status_code == 200


