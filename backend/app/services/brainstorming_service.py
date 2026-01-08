"""Service for AI-powered brainstorming with Claude."""
import logging
from typing import AsyncGenerator, Any
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

logger = logging.getLogger(__name__)


class BrainstormingService:
    """Service for brainstorming with Claude via streaming."""

    SYSTEM_PROMPT = """You are an AI co-facilitator in a product brainstorming session.

Your role:
- Help teams explore ideas and possibilities
- Ask clarifying questions to deepen thinking
- Suggest alternatives and variations
- Identify risks and opportunities
- Summarize key points when requested
- Keep discussions focused and productive

Guidelines:
- Be concise but thoughtful
- Ask one question at a time
- Acknowledge and build on user ideas
- Offer 2-3 alternatives when suggesting options
- Use web search to find relevant information when needed

You have access to WebSearch and WebFetch tools for research."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5") -> None:
        """Initialize the brainstorming service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    def _format_messages(self, messages: list[dict[str, str]]) -> list[MessageParam]:
        """Format messages for Claude API.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Formatted messages
        """
        return [
            MessageParam(role=msg["role"], content=msg["content"])  # type: ignore[typeddict-item]
            for msg in messages
        ]

    async def stream_brainstorm_message(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream a brainstorm response from Claude.

        Args:
            messages: Conversation history with role and content

        Yields:
            Text chunks from Claude's response
        """
        try:
            formatted_messages = self._format_messages(messages)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=formatted_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Error streaming brainstorm message: {e}")
            raise

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        await self.client.close()

    async def __aenter__(self) -> "BrainstormingService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
