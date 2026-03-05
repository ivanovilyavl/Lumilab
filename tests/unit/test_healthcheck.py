import pytest


@pytest.mark.asyncio
async def test_healthcheck(api_client):
    response = await api_client.get("/healthcheck")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
