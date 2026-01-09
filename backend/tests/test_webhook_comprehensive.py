"""Comprehensive tests for webhook endpoint to increase coverage."""
import pytest
import json

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feature, FeatureStatus
from app.utils.webhook_security import (
    compute_webhook_signature,
    generate_webhook_secret,
)


class TestWebhookErrors:
    """Tests for webhook error cases."""

    @pytest.mark.asyncio
    async def test_webhook_feature_not_found(self, async_client: AsyncClient):
        """Test webhook with non-existent feature returns 404."""
        payload = {
            "feature_id": "nonexistent-feature",
            "complexity": {"story_points": 5},
        }
        payload_str = json.dumps(payload)
        fake_signature = compute_webhook_signature(payload_str, "fake-secret")

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": fake_signature},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_webhook_no_webhook_secret(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test webhook when feature has no webhook secret returns 401."""
        # Create feature without webhook secret
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=None,  # No secret
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 5},
        }

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": "fake-signature"},
        )

        assert response.status_code == 401
        assert "no webhook secret configured" in response.json()["detail"].lower()


class TestWebhookFeatureStatusUpdate:
    """Tests for feature status updates via webhook."""

    @pytest.mark.asyncio
    async def test_webhook_updates_feature_to_completed(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test successful webhook updates feature status to COMPLETED."""
        secret = generate_webhook_secret()
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=secret,
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 5},
            "error": None,  # No error means success
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(payload_str, secret)

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        assert response.status_code == 200

        # Verify feature status was updated
        await db_session.refresh(feature)
        assert feature.status == FeatureStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_webhook_updates_feature_to_failed_on_error(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test webhook with error updates feature status to FAILED."""
        secret = generate_webhook_secret()
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=secret,
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {},
            "error": "Analysis failed due to timeout",  # Has error
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(payload_str, secret)

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        assert response.status_code == 200

        # Verify feature status was updated to FAILED
        await db_session.refresh(feature)
        assert feature.status == FeatureStatus.FAILED

    @pytest.mark.asyncio
    async def test_webhook_records_timestamp(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test webhook records webhook_received_at timestamp."""
        secret = generate_webhook_secret()
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=secret,
            webhook_received_at=None,  # Initially None
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 5},
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(payload_str, secret)

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        assert response.status_code == 200

        # Verify timestamp was recorded
        await db_session.refresh(feature)
        assert feature.webhook_received_at is not None


class TestWebhookAnalysisCreation:
    """Tests for analysis record creation via webhook."""

    @pytest.mark.asyncio
    async def test_webhook_creates_analysis_record(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test webhook creates an Analysis record."""
        from sqlalchemy import select
        from app.models.analysis import Analysis

        secret = generate_webhook_secret()
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=secret,
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 8, "level": "High"},
            "warnings": [{"type": "warning", "message": "Warning 1"}, {"type": "warning", "message": "Warning 2"}],
            "repository_state": {"files_changed": 5},
            "affected_modules": [{"name": "module1"}, {"name": "module2"}],
            "implementation_tasks": [{"task": "Task 1"}, {"task": "Task 2"}],
            "technical_risks": [{"risk": "Risk 1"}],
            "recommendations": {"items": ["Recommendation 1"]},
            "metadata": {"workflow_run_id": "12345"},
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(payload_str, secret)

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        assert response.status_code == 200

        # Verify Analysis record was created
        result = await db_session.execute(
            select(Analysis).where(Analysis.feature_id == feature.id)
        )
        analysis = result.scalar_one_or_none()

        assert analysis is not None
        assert analysis.feature_id == feature.id
        assert analysis.model_used == "github-workflow"
        assert analysis.result["complexity"]["story_points"] == 8
        assert len(analysis.result["warnings"]) == 2

    @pytest.mark.asyncio
    async def test_webhook_stores_all_fields(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test webhook stores all provided fields in Analysis."""
        from sqlalchemy import select
        from app.models.analysis import Analysis

        secret = generate_webhook_secret()
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=secret,
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 3, "estimated_hours": 12},
            "warnings": [{"type": "warning", "message": "Warning A"}],
            "repository_state": {"branch": "main"},
            "affected_modules": [{"name": "auth"}, {"name": "api"}],
            "implementation_tasks": [{"task": "Setup"}, {"task": "Code"}, {"task": "Test"}],
            "technical_risks": [{"risk": "Database migration"}],
            "recommendations": {"items": ["Use async"]},
            "error": None,
            "raw_output": "Raw analysis output",
            "metadata": {"version": "1.0"},
        }
        payload_str = json.dumps(payload)
        signature = compute_webhook_signature(payload_str, secret)

        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            headers={"X-Webhook-Signature": signature},
        )

        assert response.status_code == 200

        # Verify all fields stored
        result = await db_session.execute(
            select(Analysis).where(Analysis.feature_id == feature.id)
        )
        analysis = result.scalar_one_or_none()

        assert analysis.result["complexity"]["story_points"] == 3
        assert len(analysis.result["warnings"]) == 1
        assert analysis.result["warnings"][0]["message"] == "Warning A"
        assert analysis.result["repository_state"]["branch"] == "main"
        assert len(analysis.result["implementation_tasks"]) == 3
        assert analysis.result["raw_output"] == "Raw analysis output"
        assert analysis.result["metadata"]["version"] == "1.0"


class TestWebhookPayloadValidation:
    """Tests for webhook payload validation."""

    @pytest.mark.asyncio
    async def test_webhook_missing_required_header(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test webhook without X-Webhook-Signature header returns 422."""
        secret = generate_webhook_secret()
        feature = Feature(
            id="test-feature",
            name="Test Feature",
            description="Test description",
            status=FeatureStatus.ANALYZING,
            webhook_secret=secret,
        )
        db_session.add(feature)
        await db_session.commit()

        payload = {
            "feature_id": feature.id,
            "complexity": {"story_points": 5},
        }

        # Send without X-Webhook-Signature header
        response = await async_client.post(
            "/api/v1/webhooks/analysis-result",
            json=payload,
            # No headers
        )

        assert response.status_code == 422
