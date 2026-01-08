"""Service for AI-powered brainstorming with Claude Agent SDK."""
import logging
from typing import AsyncGenerator, Any
from claude_agent_sdk import Agent, AgentResponse

logger = logging.getLogger(__name__)


class BrainstormingService:
    """Service for brainstorming with Claude via streaming using Agent SDK."""

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
        self.agent = Agent(
            api_key=api_key,
            model=model,
            system_prompt=self.SYSTEM_PROMPT,
        )

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
            # Get the last user message
            if not messages:
                return

            last_message = messages[-1]["content"] if messages else ""

            # Build conversation history for context (all messages except the last one)
            conversation_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages[:-1]
            ]

            # Stream response from agent
            async for chunk in self.agent.stream(
                prompt=last_message,
                conversation_history=conversation_history,
            ):
                if isinstance(chunk, str):
                    yield chunk
                elif hasattr(chunk, 'content'):
                    yield chunk.content

        except Exception as e:
            logger.error(f"Error streaming brainstorm message: {e}")
            raise

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        # Agent SDK handles cleanup automatically
        pass

    async def __aenter__(self) -> "BrainstormingService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
