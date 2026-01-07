import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test the health check endpoint returns expected response."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Product Analysis Platform"


@pytest.mark.asyncio
async def test_health_endpoint_returns_json(async_client: AsyncClient):
    """Test the health endpoint returns valid JSON with correct content type."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
