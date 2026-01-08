"""Service for AI-powered idea evaluation with Claude Agent SDK."""
import logging
import json
import re
from typing import Any
from claude_agent_sdk import ClaudeSDKClient

logger = logging.getLogger(__name__)


class IdeaEvaluationService:
    """Service for evaluating product ideas with Claude Agent SDK."""

    SYSTEM_PROMPT = """You are an AI product analyst evaluating product ideas.

For each idea, provide:
1. Business Value (1-10): Impact on users and business metrics
2. Technical Complexity (1-10): Implementation difficulty
3. Estimated Effort: Time estimate (e.g., "2 weeks", "3 months")
4. Market Fit Analysis: How well this aligns with market needs
5. Risk Assessment: Technical and business risks

Return your evaluation as JSON with this exact structure:
{
  "business_value": <1-10>,
  "technical_complexity": <1-10>,
  "estimated_effort": "<time estimate>",
  "market_fit_analysis": "<analysis text>",
  "risk_assessment": "<risk analysis text>"
}

Be objective, concise, and data-driven in your analysis."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5") -> None:
        """Initialize the evaluation service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.agent = ClaudeSDKClient(
            api_key=api_key,
            model=model,
            system_prompt=self.SYSTEM_PROMPT,
        )

    async def evaluate_idea(
        self, title: str, description: str, context: str | None = None
    ) -> dict[str, Any]:
        """Evaluate an idea with Claude.

        Args:
            title: Idea title
            description: Idea description
            context: Optional additional context

        Returns:
            Evaluation result dict with business_value, technical_complexity, etc.

        Raises:
            Exception: If evaluation fails
        """
        try:
            # Build prompt
            prompt = f"""Evaluate this product idea:

Title: {title}

Description: {description}"""

            if context:
                prompt += f"\n\nAdditional Context: {context}"

            prompt += "\n\nProvide your evaluation as JSON."

            # Call Claude Agent
            response = await self.agent.run(prompt=prompt)

            # Extract text from response
            if isinstance(response, str):
                response_text = response
            elif hasattr(response, 'content'):
                response_text = response.content
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)

            # Parse response
            result = self._parse_evaluation_result(response_text)

            logger.info(f"Successfully evaluated idea: {title}")
            return result

        except Exception as e:
            logger.error(f"Error evaluating idea: {e}")
            raise

    def _parse_evaluation_result(self, text: str) -> dict[str, Any]:
        """Parse evaluation result from Claude response.

        Args:
            text: Claude response text

        Returns:
            Parsed evaluation dict

        Raises:
            ValueError: If parsing fails
        """
        # Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("Could not find JSON in response")

        try:
            result = json.loads(json_str)

            # Validate required fields
            required_fields = [
                "business_value",
                "technical_complexity",
                "estimated_effort",
                "market_fit_analysis",
                "risk_assessment",
            ]

            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")

            # Validate ranges
            if not (1 <= result["business_value"] <= 10):
                raise ValueError("business_value must be 1-10")
            if not (1 <= result["technical_complexity"] <= 10):
                raise ValueError("technical_complexity must be 1-10")

            return dict(result)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise ValueError(f"Invalid JSON in response: {e}")

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        # Agent SDK handles cleanup automatically
        pass

    async def __aenter__(self) -> "IdeaEvaluationService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
