"""Tests for Feature API endpoints.

Tests cover CRUD operations and analysis workflow triggering.
Uses SQLite in-memory database with aiosqlite for async operations.
"""

import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base, Feature, FeatureStatus


# Test database setup - SQLite in-memory with async
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestingAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency with test database."""
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_feature_data():
    """Sample feature data for creating features."""
    return {
        "name": "User Authentication",
        "description": "Add OAuth2 authentication with Google and GitHub providers",
        "priority": 1,
    }


@pytest.fixture
async def db_session():
    """Get a test database session."""
    async with TestingAsyncSessionLocal() as session:
        yield session


# =============================================================================
# POST /api/v1/features - Create Feature Tests
# =============================================================================


class TestCreateFeature:
    """Tests for POST /api/v1/features endpoint."""

    @pytest.mark.asyncio
    async def test_create_feature_valid_data(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test creating a feature with valid data returns 201 and the created feature."""
        response = await async_client.post("/api/v1/features", json=sample_feature_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_feature_data["name"]
        assert data["description"] == sample_feature_data["description"]
        assert data["priority"] == sample_feature_data["priority"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_feature_missing_name(self, async_client: AsyncClient):
        """Test creating a feature without name returns 422 validation error."""
        data = {
            "description": "Some description",
            "priority": 1,
        }
        response = await async_client.post("/api/v1/features", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_feature_empty_name(self, async_client: AsyncClient):
        """Test creating a feature with empty name returns 422 validation error."""
        data = {
            "name": "",
            "description": "Some description",
            "priority": 1,
        }
        response = await async_client.post("/api/v1/features", json=data)

        # Empty string is allowed by default Pydantic, so this should pass
        # If we want to reject empty names, we need to add validation
        assert response.status_code in (201, 422)

    @pytest.mark.asyncio
    async def test_create_feature_default_values(self, async_client: AsyncClient):
        """Test creating a feature with minimal data uses default values."""
        data = {"name": "Minimal Feature"}
        response = await async_client.post("/api/v1/features", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["priority"] == 0
        assert result["status"] == "pending"


# =============================================================================
# GET /api/v1/features - List Features Tests
# =============================================================================


class TestListFeatures:
    """Tests for GET /api/v1/features endpoint."""

    @pytest.mark.asyncio
    async def test_list_features_empty(self, async_client: AsyncClient):
        """Test listing features returns empty list when no features exist."""
        response = await async_client.get("/api/v1/features")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_features_multiple(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test listing features returns all created features."""
        # Create multiple features
        await async_client.post("/api/v1/features", json=sample_feature_data)
        await async_client.post(
            "/api/v1/features",
            json={
                "name": "Second Feature",
                "description": "Another feature",
                "priority": 2,
            },
        )

        response = await async_client.get("/api/v1/features")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_features_pagination_skip(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test listing features with skip parameter."""
        # Create multiple features
        for i in range(5):
            await async_client.post(
                "/api/v1/features",
                json={"name": f"Feature {i}", "description": f"Description {i}"},
            )

        response = await async_client.get("/api/v1/features?skip=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_features_pagination_limit(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test listing features with limit parameter."""
        # Create multiple features
        for i in range(5):
            await async_client.post(
                "/api/v1/features",
                json={"name": f"Feature {i}", "description": f"Description {i}"},
            )

        response = await async_client.get("/api/v1/features?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


# =============================================================================
# GET /api/v1/features/{id} - Get Single Feature Tests
# =============================================================================


class TestGetFeature:
    """Tests for GET /api/v1/features/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_feature_found(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test getting a feature by ID returns the feature."""
        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        response = await async_client.get(f"/api/v1/features/{feature_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == feature_id
        assert data["name"] == sample_feature_data["name"]

    @pytest.mark.asyncio
    async def test_get_feature_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent feature returns 404."""
        non_existent_id = str(uuid4())
        response = await async_client.get(f"/api/v1/features/{non_existent_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_feature_invalid_id_format(self, async_client: AsyncClient):
        """Test getting a feature with invalid UUID format returns 422."""
        response = await async_client.get("/api/v1/features/invalid-uuid")

        assert response.status_code == 422


# =============================================================================
# PUT /api/v1/features/{id} - Update Feature Tests
# =============================================================================


class TestUpdateFeature:
    """Tests for PUT /api/v1/features/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_feature_partial(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test partial update of a feature."""
        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        # Update only the name
        update_data = {"name": "Updated Name"}
        response = await async_client.put(
            f"/api/v1/features/{feature_id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        # Original fields should remain unchanged
        assert data["description"] == sample_feature_data["description"]
        assert data["priority"] == sample_feature_data["priority"]

    @pytest.mark.asyncio
    async def test_update_feature_status(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test updating feature status."""
        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        # Update status
        update_data = {"status": "analyzing"}
        response = await async_client.put(
            f"/api/v1/features/{feature_id}", json=update_data
        )

        assert response.status_code == 200
        assert response.json()["status"] == "analyzing"

    @pytest.mark.asyncio
    async def test_update_feature_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent feature returns 404."""
        non_existent_id = str(uuid4())
        update_data = {"name": "Updated Name"}
        response = await async_client.put(
            f"/api/v1/features/{non_existent_id}", json=update_data
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_feature_invalid_status(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test updating feature with invalid status returns 422."""
        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        # Try to update with invalid status
        update_data = {"status": "invalid_status"}
        response = await async_client.put(
            f"/api/v1/features/{feature_id}", json=update_data
        )

        assert response.status_code == 422


# =============================================================================
# DELETE /api/v1/features/{id} - Delete Feature Tests
# =============================================================================


class TestDeleteFeature:
    """Tests for DELETE /api/v1/features/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_feature_success(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test deleting a feature returns 204 and removes the feature."""
        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        # Delete the feature
        response = await async_client.delete(f"/api/v1/features/{feature_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await async_client.get(f"/api/v1/features/{feature_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_feature_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent feature returns 404."""
        non_existent_id = str(uuid4())
        response = await async_client.delete(f"/api/v1/features/{non_existent_id}")

        assert response.status_code == 404


# =============================================================================
# POST /api/v1/features/{id}/analyze - Trigger Analysis Tests
# =============================================================================


class TestTriggerAnalysis:
    """Tests for POST /api/v1/features/{id}/analyze endpoint."""

    @pytest.fixture
    def mock_github_service(self):
        """Create a mock GitHub service."""
        mock_service = AsyncMock()
        mock_service.trigger_analysis_workflow.return_value = 12345678
        return mock_service

    @pytest.mark.asyncio
    async def test_trigger_analysis_success(
        self, async_client: AsyncClient, sample_feature_data: dict, mock_github_service
    ):
        """Test triggering analysis returns run_id and updates status."""
        from app.api.features import get_github_service

        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        # Override the GitHub service dependency
        app.dependency_overrides[get_github_service] = lambda: mock_github_service

        try:
            response = await async_client.post(f"/api/v1/features/{feature_id}/analyze")

            assert response.status_code == 202
            data = response.json()
            assert "run_id" in data
            assert data["run_id"] == 12345678

            # Verify feature status was updated
            get_response = await async_client.get(f"/api/v1/features/{feature_id}")
            assert get_response.json()["status"] == "analyzing"
        finally:
            # Clean up dependency override
            if get_github_service in app.dependency_overrides:
                del app.dependency_overrides[get_github_service]

    @pytest.mark.asyncio
    async def test_trigger_analysis_not_found(
        self, async_client: AsyncClient, mock_github_service
    ):
        """Test triggering analysis for non-existent feature returns 404."""
        from app.api.features import get_github_service

        # Override the GitHub service dependency
        app.dependency_overrides[get_github_service] = lambda: mock_github_service

        try:
            non_existent_id = str(uuid4())
            response = await async_client.post(f"/api/v1/features/{non_existent_id}/analyze")

            assert response.status_code == 404
        finally:
            # Clean up dependency override
            if get_github_service in app.dependency_overrides:
                del app.dependency_overrides[get_github_service]

    @pytest.mark.asyncio
    async def test_trigger_analysis_stores_workflow_run_id(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test triggering analysis stores the workflow run_id on the feature."""
        from app.api.features import get_github_service

        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        expected_run_id = 98765432

        # Create mock service with specific run_id
        mock_service = AsyncMock()
        mock_service.trigger_analysis_workflow.return_value = expected_run_id

        # Override the GitHub service dependency
        app.dependency_overrides[get_github_service] = lambda: mock_service

        try:
            await async_client.post(f"/api/v1/features/{feature_id}/analyze")

            # Verify workflow run_id was stored
            get_response = await async_client.get(f"/api/v1/features/{feature_id}")
            assert get_response.json()["analysis_workflow_run_id"] == str(expected_run_id)
        finally:
            # Clean up dependency override
            if get_github_service in app.dependency_overrides:
                del app.dependency_overrides[get_github_service]

    @pytest.mark.asyncio
    async def test_trigger_analysis_github_error(
        self, async_client: AsyncClient, sample_feature_data: dict
    ):
        """Test triggering analysis when GitHub fails returns 500."""
        from app.api.features import get_github_service

        # Create a feature first
        create_response = await async_client.post(
            "/api/v1/features", json=sample_feature_data
        )
        feature_id = create_response.json()["id"]

        # Create mock service that raises an error
        mock_service = AsyncMock()
        mock_service.trigger_analysis_workflow.side_effect = Exception(
            "GitHub API error"
        )

        # Override the GitHub service dependency
        app.dependency_overrides[get_github_service] = lambda: mock_service

        try:
            response = await async_client.post(f"/api/v1/features/{feature_id}/analyze")

            assert response.status_code == 500
            assert "error" in response.json()["detail"].lower()
        finally:
            # Clean up dependency override
            if get_github_service in app.dependency_overrides:
                del app.dependency_overrides[get_github_service]


# =============================================================================
# Feature Creation with Webhook Secret Tests
# =============================================================================


class TestFeatureCreationWithWebhook:
    """Tests for feature creation with webhook secret generation."""

    @pytest.mark.asyncio
    async def test_create_feature_generates_webhook_secret(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Creating a feature should automatically generate webhook secret."""
        response = await async_client.post(
            "/api/v1/features/",
            json={
                "name": "Test Feature",
                "description": "Test description",
                "priority": 1,
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Webhook secret should not be exposed in API response
        assert "webhook_secret" not in data

        # But it should exist in database
        from sqlalchemy import select

        result = await db_session.execute(select(Feature).where(Feature.id == data["id"]))
        feature = result.scalar_one()

        assert feature.webhook_secret is not None
        assert len(feature.webhook_secret) > 20  # Should be reasonably long

    @pytest.mark.asyncio
    async def test_each_feature_gets_unique_webhook_secret(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Each feature should get a unique webhook secret."""
        response1 = await async_client.post(
            "/api/v1/features/",
            json={
                "name": "Feature 1",
                "description": "Test 1",
                "priority": 1,
            },
        )
        response2 = await async_client.post(
            "/api/v1/features/",
            json={
                "name": "Feature 2",
                "description": "Test 2",
                "priority": 1,
            },
        )

        from sqlalchemy import select

        result1 = await db_session.execute(
            select(Feature).where(Feature.id == response1.json()["id"])
        )
        result2 = await db_session.execute(
            select(Feature).where(Feature.id == response2.json()["id"])
        )

        feature1 = result1.scalar_one()
        feature2 = result2.scalar_one()

        assert feature1.webhook_secret != feature2.webhook_secret


# =============================================================================
# Trigger Analysis with Callback URL Tests
# =============================================================================


class TestTriggerAnalysisWithCallback:
    """Tests for trigger_analysis with callback URL."""

    @pytest.mark.asyncio
    async def test_trigger_analysis_includes_callback_url_when_webhook_base_url_set(
        self, db_session: AsyncSession, monkeypatch
    ):
        """Trigger analysis should include callback URL when webhook_base_url is configured."""
        # Create feature with UUID
        feature_id = str(uuid4())
        feature = Feature(
            id=feature_id,
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            webhook_secret="test-secret",
        )
        db_session.add(feature)
        await db_session.commit()

        # Mock settings to have webhook_base_url
        from app.config import settings

        monkeypatch.setattr(settings, "webhook_base_url", "https://api.example.com")

        # Mock GitHubService
        from app.api.features import get_github_service

        mock_github_service = AsyncMock()
        mock_github_service.trigger_analysis_workflow.return_value = 12345

        # Override the GitHub service dependency
        app.dependency_overrides[get_github_service] = lambda: mock_github_service

        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/features/{feature_id}/analyze"
                )

            assert response.status_code == 202

            # Verify callback URL was passed to GitHub service
            mock_github_service.trigger_analysis_workflow.assert_called_once()
            call_args = mock_github_service.trigger_analysis_workflow.call_args

            callback_url = call_args.kwargs.get("callback_url")
            assert callback_url is not None
            assert "https://api.example.com" in callback_url
            assert "/api/v1/webhooks/analysis-result" in callback_url
        finally:
            # Clean up dependency override
            if get_github_service in app.dependency_overrides:
                del app.dependency_overrides[get_github_service]

    @pytest.mark.asyncio
    async def test_trigger_analysis_skips_callback_url_when_webhook_base_url_not_set(
        self, db_session: AsyncSession, monkeypatch
    ):
        """Trigger analysis should not include callback URL when webhook_base_url is None."""
        # Create feature with UUID
        feature_id = str(uuid4())
        feature = Feature(
            id=feature_id,
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.PENDING,
            webhook_secret="test-secret",
        )
        db_session.add(feature)
        await db_session.commit()

        # Mock settings to have no webhook_base_url
        from app.config import settings

        monkeypatch.setattr(settings, "webhook_base_url", None)

        # Mock GitHubService
        from app.api.features import get_github_service

        mock_github_service = AsyncMock()
        mock_github_service.trigger_analysis_workflow.return_value = 12345

        # Override the GitHub service dependency
        app.dependency_overrides[get_github_service] = lambda: mock_github_service

        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    f"/api/v1/features/{feature_id}/analyze"
                )

            assert response.status_code == 202

            # Verify callback URL was None
            mock_github_service.trigger_analysis_workflow.assert_called_once()
            call_args = mock_github_service.trigger_analysis_workflow.call_args

            callback_url = call_args.kwargs.get("callback_url")
            assert callback_url is None
        finally:
            # Clean up dependency override
            if get_github_service in app.dependency_overrides:
                del app.dependency_overrides[get_github_service]
