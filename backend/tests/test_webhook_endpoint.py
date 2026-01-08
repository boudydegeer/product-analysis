"""Tests for webhook endpoint."""
import pytest
import json
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base, Feature, FeatureStatus
from app.utils.webhook_security import (
    compute_webhook_signature,
    generate_webhook_secret,
)


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

        # Reload feature with analyses eagerly loaded
        result = await db_session.execute(
            select(Feature)
            .where(Feature.id == test_feature_with_webhook.id)
            .options(selectinload(Feature.analyses))
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


@pytest.mark.asyncio
async def test_webhook_extracts_flattened_fields_from_real_workflow_structure(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Should extract and populate all 13 flattened fields from REAL workflow structure.

    This test uses the ACTUAL structure that the GitHub workflow generates,
    NOT the incorrect structure with complexity.summary and complexity.implementation.
    """
    from app.models.analysis import Analysis
    from sqlalchemy import select

    # Create feature
    feature = Feature(
        id="webhook-real-structure",
        name="Webhook Real Structure Test",
        description="Testing with real workflow structure",
        status=FeatureStatus.ANALYZING,
        webhook_secret="test-secret-real",
    )
    db_session.add(feature)
    await db_session.commit()

    # Prepare webhook payload with REAL workflow structure
    payload = {
        "feature_id": "webhook-real-structure",
        "warnings": [
            {
                "type": "missing_infrastructure",
                "severity": "high",
                "message": "Backend infrastructure missing",
                "impact": "Increases estimate significantly",
            }
        ],
        "repository_state": {
            "has_backend_code": True,
            "has_frontend_code": True,
            "has_database_models": True,
            "has_authentication": False,
            "maturity_level": "partial",
            "notes": "Core infrastructure exists but auth missing",
        },
        "complexity": {
            "story_points": 13,
            "estimated_hours": 24,
            "prerequisite_hours": 16,
            "total_hours": 40,
            "level": "High",
            "rationale": "Requires significant backend and frontend changes",
        },
        "affected_modules": [
            {
                "path": "backend/app/api/features.py",
                "change_type": "modify",
                "reason": "Add new endpoint",
            },
            {
                "path": "frontend/src/components/FeatureForm.vue",
                "change_type": "modify",
                "reason": "Add UI for new feature",
            },
        ],
        "implementation_tasks": [
            {
                "id": "task-1",
                "task_type": "prerequisite",
                "description": "Setup authentication system",
                "estimated_effort_hours": 16,
                "dependencies": [],
                "priority": "high",
            },
            {
                "id": "task-2",
                "task_type": "feature",
                "description": "Implement API endpoint",
                "estimated_effort_hours": 12,
                "dependencies": ["task-1"],
                "priority": "high",
            },
            {
                "id": "task-3",
                "task_type": "feature",
                "description": "Build frontend UI",
                "estimated_effort_hours": 12,
                "dependencies": ["task-2"],
                "priority": "medium",
            },
        ],
        "technical_risks": [
            {
                "category": "security",
                "description": "Authentication bypass vulnerability",
                "severity": "critical",
                "mitigation": "Implement proper JWT validation with refresh tokens",
            },
            {
                "category": "performance",
                "description": "Database query N+1 problem",
                "severity": "medium",
                "mitigation": "Use eager loading with selectinload",
            },
            {
                "category": "scalability",
                "description": "High memory usage with large datasets",
                "severity": "high",
                "mitigation": "Implement pagination and streaming",
            },
        ],
        "recommendations": {
            "approach": "Start with authentication infrastructure, then build feature incrementally",
            "alternatives": [
                "Use OAuth provider like Auth0",
                "Implement custom JWT auth",
            ],
            "testing_strategy": "Unit tests for business logic, integration tests for API, E2E for critical flows",
            "deployment_notes": "Requires database migration and environment variable updates",
        },
        "error": None,
        "raw_output": "Analysis completed successfully",
        "metadata": {
            "analyzed_at": "2024-01-15T10:00:00Z",
            "workflow_run_id": "67890",
            "model": "claude-3-5-sonnet-20241022",
        },
    }

    payload_str = json.dumps(payload)
    signature = compute_webhook_signature(payload_str, "test-secret-real")

    # Send webhook
    response = await async_client.post(
        "/api/v1/webhooks/analysis-result",
        json=payload,
        headers={"X-Webhook-Signature": signature},
    )

    assert response.status_code == 200

    # Verify flattened data was extracted and saved
    result = await db_session.execute(
        select(Analysis).where(Analysis.feature_id == "webhook-real-structure")
    )
    analysis = result.scalar_one()

    # Verify flattened summary fields (from complexity)
    assert analysis.summary_overview == "High"
    assert analysis.summary_key_points == [
        "Requires significant backend and frontend changes"
    ]
    assert analysis.summary_metrics == {
        "story_points": 13,
        "estimated_hours": 24,
        "prerequisite_hours": 16,
        "total_hours": 40,
    }

    # Verify flattened implementation fields (from implementation_tasks + affected_modules)
    assert analysis.implementation_architecture == {
        "affected_modules_count": 2,
        "primary_areas": [
            "backend/app/api/features.py",
            "frontend/src/components/FeatureForm.vue",
        ],
    }
    assert len(analysis.implementation_technical_details) == 3
    assert analysis.implementation_technical_details[0]["id"] == "task-1"
    assert analysis.implementation_technical_details[1]["id"] == "task-2"
    assert analysis.implementation_technical_details[2]["id"] == "task-3"
    assert analysis.implementation_data_flow == {
        "has_prerequisites": True,
        "prerequisite_count": 1,
        "feature_task_count": 2,
    }

    # Verify flattened risk fields (from technical_risks)
    assert len(analysis.risks_technical_risks) == 3
    assert analysis.risks_technical_risks[0]["category"] == "security"

    # Security concerns extracted from technical_risks
    assert len(analysis.risks_security_concerns) == 1
    assert analysis.risks_security_concerns[0]["severity"] == "critical"

    # Scalability issues extracted from technical_risks
    assert len(analysis.risks_scalability_issues) == 1
    assert (
        analysis.risks_scalability_issues[0]["description"]
        == "High memory usage with large datasets"
    )

    # Mitigation strategies extracted from technical_risks
    assert len(analysis.risks_mitigation_strategies) == 3
    assert (
        "Implement proper JWT validation with refresh tokens"
        in analysis.risks_mitigation_strategies
    )

    # Verify flattened recommendation fields (from recommendations)
    assert len(analysis.recommendations_improvements) == 2
    assert "OAuth provider like Auth0" in analysis.recommendations_improvements[0]

    assert len(analysis.recommendations_best_practices) >= 1
    assert any(
        "Unit tests" in practice for practice in analysis.recommendations_best_practices
    )

    assert len(analysis.recommendations_next_steps) >= 1
    assert "Start with authentication" in analysis.recommendations_next_steps[0]
