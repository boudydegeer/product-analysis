import pytest
from httpx import AsyncClient
from unittest.mock import patch


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


@pytest.mark.asyncio
async def test_root_endpoint_exists():
    """Test that root endpoint is defined in app."""
    from app.main import app
    # Check that the root endpoint is defined
    routes = [route.path for route in app.routes]
    assert "/" in routes


@pytest.mark.asyncio
async def test_lifespan_startup_shutdown():
    """Test that lifespan starts and stops scheduler."""
    from app.main import lifespan, app

    with patch("app.main.start_polling_scheduler") as mock_start:
        with patch("app.main.stop_polling_scheduler") as mock_stop:
            async with lifespan(app):
                # Startup should call start_polling_scheduler
                mock_start.assert_called_once()

            # Shutdown should call stop_polling_scheduler
            mock_stop.assert_called_once()


@pytest.mark.asyncio
async def test_cors_middleware_applied(async_client: AsyncClient):
    """Test that CORS middleware is applied."""
    response = await async_client.get("/health", headers={"Origin": "http://localhost:8892"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_app_metadata():
    """Test app metadata is set correctly."""
    from app.main import app
    from app.config import settings

    assert app.title == settings.app_name
    assert app.debug == settings.debug
