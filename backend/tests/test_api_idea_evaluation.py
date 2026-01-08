"""Tests for idea evaluation endpoint."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestEvaluateIdea:
    """Tests for POST /api/v1/ideas/evaluate endpoint."""

    @pytest.mark.asyncio
    async def test_evaluate_idea_success(self, async_client: AsyncClient):
        """Test evaluating an idea with AI."""
        data = {
            "title": "Dark Mode Feature",
            "description": "Add dark mode support to the application",
        }

        # Mock IdeaEvaluationService
        mock_evaluation = {
            "business_value": 8,
            "technical_complexity": 5,
            "estimated_effort": "2 weeks",
            "market_fit_analysis": "Strong demand based on user feedback",
            "risk_assessment": "Low risk - standard UI implementation",
        }

        with patch("app.api.ideas.IdeaEvaluationService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.evaluate_idea = AsyncMock(return_value=mock_evaluation)

            response = await async_client.post("/api/v1/ideas/evaluate", json=data)

            assert response.status_code == 200
            result = response.json()
            assert result["business_value"] == 8
            assert result["technical_complexity"] == 5
            assert result["estimated_effort"] == "2 weeks"

    @pytest.mark.asyncio
    async def test_evaluate_idea_with_context(self, async_client: AsyncClient):
        """Test evaluating idea with additional context."""
        data = {
            "title": "Mobile Redesign",
            "description": "Redesign mobile app",
            "context": "Users have requested this feature 50+ times",
        }

        mock_evaluation = {
            "business_value": 9,
            "technical_complexity": 7,
            "estimated_effort": "3 months",
            "market_fit_analysis": "Very strong demand",
            "risk_assessment": "Medium risk - large scope",
        }

        with patch("app.api.ideas.IdeaEvaluationService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = AsyncMock()
            mock_instance.evaluate_idea = AsyncMock(return_value=mock_evaluation)

            response = await async_client.post("/api/v1/ideas/evaluate", json=data)

            assert response.status_code == 200
            mock_instance.evaluate_idea.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_idea_api_key_missing(self, async_client: AsyncClient):
        """Test evaluation fails if API key not configured."""
        data = {
            "title": "Test Idea",
            "description": "Test description",
        }

        with patch("app.api.ideas.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""

            response = await async_client.post("/api/v1/ideas/evaluate", json=data)

            assert response.status_code == 500
            assert "API key not configured" in response.json()["detail"]
