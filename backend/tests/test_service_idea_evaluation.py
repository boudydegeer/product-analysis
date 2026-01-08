"""Tests for idea evaluation service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.idea_evaluation_service import IdeaEvaluationService


class TestIdeaEvaluationService:
    """Tests for IdeaEvaluationService."""

    @pytest.mark.asyncio
    async def test_evaluate_idea(self):
        """Test evaluating an idea with Claude."""
        service = IdeaEvaluationService(api_key="test-key")

        title = "Dark Mode Feature"
        description = "Add dark mode support to the application"

        # Mock the Anthropic client
        with patch.object(service, 'client') as mock_client:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(
                    text='{"business_value": 8, "technical_complexity": 5, "estimated_effort": "2 weeks", "market_fit_analysis": "Strong demand", "risk_assessment": "Low risk"}'
                )
            ]
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await service.evaluate_idea(title, description)

            assert result["business_value"] == 8
            assert result["technical_complexity"] == 5
            assert result["estimated_effort"] == "2 weeks"

    def test_parse_evaluation_result(self):
        """Test parsing JSON evaluation result."""
        service = IdeaEvaluationService(api_key="test-key")

        text = '{"business_value": 8, "technical_complexity": 5, "estimated_effort": "2 weeks", "market_fit_analysis": "Strong", "risk_assessment": "Low"}'

        result = service._parse_evaluation_result(text)

        assert result["business_value"] == 8
        assert result["technical_complexity"] == 5

    def test_parse_evaluation_result_with_markdown(self):
        """Test parsing result with markdown code block."""
        service = IdeaEvaluationService(api_key="test-key")

        text = '''Here's my evaluation:

```json
{
  "business_value": 8,
  "technical_complexity": 5,
  "estimated_effort": "2 weeks",
  "market_fit_analysis": "Strong demand based on user feedback",
  "risk_assessment": "Low risk - standard implementation"
}
```

This looks like a good idea!'''

        result = service._parse_evaluation_result(text)

        assert result["business_value"] == 8
        assert result["technical_complexity"] == 5
