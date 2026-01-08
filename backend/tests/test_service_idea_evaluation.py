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

        # Create message objects with content attribute
        class MockTextBlock:
            def __init__(self, text):
                self.text = text

        class MockMessage:
            def __init__(self, json_response):
                self.content = [MockTextBlock(json_response)]

        # Create async iterator for receive_messages()
        async def mock_receive_messages():
            # Yield message object with content attribute containing JSON response
            json_response = '{"business_value": 8, "technical_complexity": 5, "estimated_effort": "2 weeks", "market_fit_analysis": "Strong demand", "risk_assessment": "Low risk"}'
            yield MockMessage(json_response)

        # Mock the claude-agent-sdk client methods
        mock_connect = AsyncMock()
        mock_query = AsyncMock()

        with patch.object(service.client, "connect", mock_connect):
            with patch.object(service.client, "query", mock_query):
                with patch.object(
                    service.client,
                    "receive_messages",
                    MagicMock(return_value=mock_receive_messages())
                ):
                    result = await service.evaluate_idea(title, description)

                    assert result["business_value"] == 8
                    assert result["technical_complexity"] == 5
                    assert result["estimated_effort"] == "2 weeks"

                    # Verify client methods were called
                    mock_connect.assert_awaited_once()
                    mock_query.assert_awaited_once()

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

        text = """Here's my evaluation:

```json
{
  "business_value": 8,
  "technical_complexity": 5,
  "estimated_effort": "2 weeks",
  "market_fit_analysis": "Strong demand based on user feedback",
  "risk_assessment": "Low risk - standard implementation"
}
```

This looks like a good idea!"""

        result = service._parse_evaluation_result(text)

        assert result["business_value"] == 8
        assert result["technical_complexity"] == 5
