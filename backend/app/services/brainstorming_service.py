"""Service for AI-powered brainstorming with Claude Agent SDK."""
import logging
import os
from typing import AsyncGenerator, Any
from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions

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

        # Set API key in environment for Claude SDK
        os.environ['ANTHROPIC_API_KEY'] = api_key

        # Initialize client with options
        options = ClaudeAgentOptions(
            model=model,
            system_prompt=self.SYSTEM_PROMPT,
        )
        self.client = ClaudeSDKClient(options=options)
        self.connected = False

    async def _ensure_connected(self):
        """Ensure client is connected."""
        if not self.connected:
            await self.client.connect()
            self.connected = True

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
            # Ensure client is connected
            await self._ensure_connected()

            # Build the prompt from the conversation history
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Assistant: {content}")

            prompt = "\n\n".join(prompt_parts)

            # Send query (non-blocking)
            await self.client.query(prompt)

            # Receive messages in streaming mode
            async for message in self.client.receive_messages():
                # Extract text from different message types
                if hasattr(message, 'content'):
                    if isinstance(message.content, str):
                        yield message.content
                    elif isinstance(message.content, list):
                        # Handle content blocks
                        for block in message.content:
                            if hasattr(block, 'text'):
                                yield block.text
                            elif isinstance(block, dict) and 'text' in block:
                                yield block['text']
                elif hasattr(message, 'text'):
                    yield message.text
                elif hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                    # Stream event with delta
                    yield message.delta.text

        except Exception as e:
            logger.error(f"Error streaming brainstorm message: {e}")
            raise

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        if self.connected:
            await self.client.disconnect()
            self.connected = False

    async def __aenter__(self) -> "BrainstormingService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
