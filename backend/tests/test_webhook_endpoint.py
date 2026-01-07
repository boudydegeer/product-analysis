"""Tests for webhook endpoint."""
import pytest
import json
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base, Feature, FeatureStatus
from app.utils.webhook_security import compute_webhook_signature, generate_webhook_secret


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
async def db_session():
    """Get a test database session."""
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def test_feature_with_webhook(db_session: AsyncSession):
    """Create a test feature with webhook secret for testing."""
    secret = generate_webhook_secret()
    feature = Feature(
        id="test-feature-123",
        name="Test Feature",
        description="Test description",
        status=FeatureStatus.ANALYZING,
        priority=1,
        webhook_secret=secret,
    )
    db_session.add(feature)
    await db_session.commit()
    await db_session.refresh(feature)
    return feature


class TestWebhookEndpoint:
    """Tests for POST /api/v1/webhooks/analysis-result endpoint."""

    @pytest.mark.anyio
    async def test_webhook_accepts_valid_result(
        self, async_client: AsyncClient, test_feature_with_webhook: Feature
    ):
        """Should accept webhook with valid signature and payload."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
                "level": "Medium",
            },
            "metadata": {
                "workflow_run_id": "12345",
                "repository": "owner/repo",
            },
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(
            payload_str, test_feature_with_webhook.webhook_secret
        )

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["feature_id"] == test_feature_with_webhook.id

    @pytest.mark.anyio
    async def test_webhook_rejects_invalid_signature(
        self, async_client: AsyncClient, test_feature_with_webhook: Feature
    ):
        """Should reject webhook with invalid signature."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "complexity": {"story_points": 5},
        }
        invalid_signature = "0" * 64  # Invalid signature

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": invalid_signature},
        )

        # Assert
        assert response.status_code == 401
        assert "signature" in response.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_webhook_rejects_missing_signature(
        self, async_client: AsyncClient, test_feature_with_webhook: Feature
    ):
        """Should reject webhook without signature header."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "complexity": {"story_points": 5},
        }

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
        )

        # Assert
        assert response.status_code == 422  # Missing required header

    @pytest.mark.anyio
    async def test_webhook_handles_feature_not_found(self, async_client: AsyncClient):
        """Should return 404 if feature doesn't exist."""
        # Arrange
        payload = {
            "feature_id": "nonexistent-feature",
            "complexity": {"story_points": 5},
        }
        payload_str = json.dumps(payload)
        secret = "test-secret"
        signature = compute_webhook_signature(payload_str, secret)

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_webhook_handles_error_payload(
        self,
        async_client: AsyncClient,
        test_feature_with_webhook: Feature,
        db_session: AsyncSession,
    ):
        """Should handle webhook payload with error field."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "error": "Analysis timeout",
            "metadata": {
                "workflow_run_id": "12345",
            },
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(
            payload_str, test_feature_with_webhook.webhook_secret
        )

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify feature status was updated to FAILED
        await db_session.refresh(test_feature_with_webhook)
        assert test_feature_with_webhook.status == FeatureStatus.FAILED

    @pytest.mark.anyio
    async def test_webhook_updates_feature_status_on_success(
        self,
        async_client: AsyncClient,
        test_feature_with_webhook: Feature,
        db_session: AsyncSession,
    ):
        """Should update feature status to COMPLETED when result received."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "complexity": {"story_points": 5},
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(
            payload_str, test_feature_with_webhook.webhook_secret
        )

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 200

        # Verify feature status was updated
        await db_session.refresh(test_feature_with_webhook)
        assert test_feature_with_webhook.status == FeatureStatus.COMPLETED

    @pytest.mark.anyio
    async def test_webhook_updates_feature_status_on_error(
        self,
        async_client: AsyncClient,
        test_feature_with_webhook: Feature,
        db_session: AsyncSession,
    ):
        """Should update feature status to FAILED when error received."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "error": "Analysis failed",
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(
            payload_str, test_feature_with_webhook.webhook_secret
        )

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 200

        # Verify feature status was updated
        await db_session.refresh(test_feature_with_webhook)
        assert test_feature_with_webhook.status == FeatureStatus.FAILED

    @pytest.mark.anyio
    async def test_webhook_stores_received_timestamp(
        self,
        async_client: AsyncClient,
        test_feature_with_webhook: Feature,
        db_session: AsyncSession,
    ):
        """Should store webhook_received_at timestamp."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "complexity": {"story_points": 5},
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(
            payload_str, test_feature_with_webhook.webhook_secret
        )

        # Initial state
        assert test_feature_with_webhook.webhook_received_at is None

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 200

        # Verify timestamp was recorded
        await db_session.refresh(test_feature_with_webhook)
        assert test_feature_with_webhook.webhook_received_at is not None

    @pytest.mark.anyio
    async def test_webhook_creates_analysis_record(
        self,
        async_client: AsyncClient,
        test_feature_with_webhook: Feature,
        db_session: AsyncSession,
    ):
        """Should create Analysis record with result data."""
        # Arrange
        payload = {
            "feature_id": test_feature_with_webhook.id,
            "complexity": {
                "story_points": 5,
                "estimated_hours": 16,
            },
            "warnings": [{"type": "test", "message": "Test warning"}],
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(
            payload_str, test_feature_with_webhook.webhook_secret
        )

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 200

        # Verify Analysis record was created
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models import Analysis

        # Reload feature with analyses eagerly loaded
        result = await db_session.execute(
            select(Feature).where(Feature.id == test_feature_with_webhook.id).options(selectinload(Feature.analyses))
        )
        feature = result.scalar_one()

        assert len(feature.analyses) == 1

        analysis = feature.analyses[0]
        assert analysis.result["complexity"]["story_points"] == 5
        assert len(analysis.result["warnings"]) == 1

    @pytest.mark.anyio
    async def test_webhook_validates_payload_schema(self, async_client: AsyncClient):
        """Should validate payload matches AnalysisResultWebhook schema."""
        # Arrange
        payload = {
            # Missing required feature_id field
            "complexity": {"story_points": 5},
        }
        payload_str = json.dumps(payload)
        secret = "test-secret"
        signature = compute_webhook_signature(payload_str, secret)

        # Act
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        # Assert
        assert response.status_code == 422  # Validation error
