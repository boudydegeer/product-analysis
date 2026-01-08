"""Tests for webhook schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.webhook import AnalysisResultWebhook


class TestAnalysisResultWebhook:
    """Tests for AnalysisResultWebhook schema."""

    def test_webhook_parses_valid_payload(self):
        """Should parse valid webhook payload from GitHub workflow."""
        payload = {
            "feature_id": "test-123",
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

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.feature_id == "test-123"
        assert webhook.complexity["story_points"] == 5
        assert webhook.metadata["workflow_run_id"] == "12345"

    def test_webhook_requires_feature_id(self):
        """Feature ID is required in webhook payload."""
        payload = {
            "complexity": {"story_points": 5},
        }

        with pytest.raises(ValidationError) as exc_info:
            AnalysisResultWebhook(**payload)

        assert "feature_id" in str(exc_info.value)

    def test_webhook_accepts_error_field(self):
        """Webhook should accept error field for failed analyses."""
        payload = {
            "feature_id": "test-123",
            "error": "Analysis timeout",
            "metadata": {
                "workflow_run_id": "12345",
            },
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.error == "Analysis timeout"
        assert webhook.feature_id == "test-123"

    def test_webhook_metadata_is_optional(self):
        """Metadata field should be optional."""
        payload = {
            "feature_id": "test-123",
            "complexity": {"story_points": 3},
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.feature_id == "test-123"
        assert webhook.metadata is None

    def test_webhook_preserves_full_result_structure(self):
        """Webhook should preserve the complete result structure."""
        payload = {
            "feature_id": "test-123",
            "warnings": [
                {
                    "type": "missing_infrastructure",
                    "severity": "high",
                    "message": "No backend code found",
                }
            ],
            "repository_state": {
                "has_backend_code": False,
                "maturity_level": "empty",
            },
            "complexity": {
                "story_points": 8,
                "estimated_hours": 24,
            },
            "affected_modules": [{"path": "src/api.py", "change_type": "new"}],
            "implementation_tasks": [
                {
                    "id": "task-1",
                    "description": "Setup backend",
                    "task_type": "prerequisite",
                }
            ],
            "technical_risks": [{"category": "security", "severity": "medium"}],
            "recommendations": {
                "approach": "Start with MVP",
                "alternatives": ["Use existing framework"],
            },
            "metadata": {
                "workflow_run_id": "12345",
                "analyzed_at": "2026-01-07T10:00:00Z",
            },
        }

        webhook = AnalysisResultWebhook(**payload)

        assert webhook.feature_id == "test-123"
        assert len(webhook.warnings) == 1
        assert webhook.repository_state["maturity_level"] == "empty"
        assert len(webhook.implementation_tasks) == 1
