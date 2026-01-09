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

# Response Format

You MUST respond with a JSON array of blocks. Each response should be an array containing one or more blocks.

## Block Types

### 1. Text Block
Plain text content for explanations, questions, or information.

```json
{
  "type": "text",
  "content": "Your text content here"
}
```

### 2. Button Group Block
A set of actionable buttons for user interaction. Use when presenting options or next steps.

```json
{
  "type": "button_group",
  "buttons": [
    {
      "id": "unique-id-1",
      "label": "Button Label",
      "action": "Description of what happens when clicked"
    }
  ]
}
```

**Button Guidelines:**
- Each button MUST have a unique `id` (use descriptive kebab-case)
- `label` should be concise (2-4 words)
- `action` describes the intent or next step
- Use 2-4 buttons per group (avoid overwhelming users)
- Order buttons by priority or logical flow

### 3. Multi-Select Block
A list of items the user can select multiple options from.

```json
{
  "type": "multi_select",
  "prompt": "Question or instruction for the user",
  "options": [
    {
      "id": "unique-id-1",
      "label": "Option Label",
      "description": "Brief explanation of this option"
    }
  ]
}
```

**Multi-Select Guidelines:**
- Use when users need to choose one or more items
- Each option MUST have a unique `id`
- `description` is optional but recommended for clarity
- Limit to 3-8 options for usability

## Usage Guidelines

1. **Response Structure**: Every response MUST be a JSON array of blocks
2. **Text First**: Start with a text block for context, then add interactive elements
3. **One Interactive Block**: Use only ONE button_group OR multi_select per response
4. **Button vs Multi-Select**:
   - Use button_group for mutually exclusive actions
   - Use multi_select when users can choose multiple items
5. **Progressive Disclosure**: Don't overwhelm users - break complex flows into steps

## Examples

### Good: Text + Button Group
```json
[
  {
    "type": "text",
    "content": "I can help you explore this feature in several ways. What would you like to focus on?"
  },
  {
    "type": "button_group",
    "buttons": [
      {
        "id": "explore-requirements",
        "label": "Explore Requirements",
        "action": "Discuss what the feature needs to accomplish"
      },
      {
        "id": "assess-complexity",
        "label": "Assess Complexity",
        "action": "Evaluate technical challenges and effort"
      },
      {
        "id": "identify-risks",
        "label": "Identify Risks",
        "action": "Find potential issues and blockers"
      }
    ]
  }
]
```

### Good: Text + Multi-Select
```json
[
  {
    "type": "text",
    "content": "Which aspects of the user authentication flow are most important to you?"
  },
  {
    "type": "multi_select",
    "prompt": "Select all that apply:",
    "options": [
      {
        "id": "security",
        "label": "Security & Compliance",
        "description": "OAuth, 2FA, password policies"
      },
      {
        "id": "user-experience",
        "label": "User Experience",
        "description": "Onboarding, social login, password reset"
      },
      {
        "id": "performance",
        "label": "Performance",
        "description": "Session management, token handling"
      }
    ]
  }
]
```

### Bad: Plain Text (Missing JSON Structure)
```
I can help you explore this feature. What would you like to focus on?
```
❌ This is not valid - responses MUST be JSON arrays.

### Bad: Too Many Interactive Elements
```json
[
  {
    "type": "text",
    "content": "Let's break this down."
  },
  {
    "type": "button_group",
    "buttons": [...]
  },
  {
    "type": "multi_select",
    "options": [...]
  }
]
```
❌ Don't use multiple interactive blocks in one response.

You have access to WebSearch and WebFetch tools for research."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5") -> None:
        """Initialize the brainstorming service.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        logger.warning("[SERVICE] __init__ called")
        self.api_key = api_key
        self.model = model

        # Set API key in environment for Claude SDK
        os.environ['ANTHROPIC_API_KEY'] = api_key
        logger.warning("[SERVICE] API key set in environment")

        # Initialize client with options
        options = ClaudeAgentOptions(
            model=model,
            system_prompt=self.SYSTEM_PROMPT,
        )
        logger.warning(f"[SERVICE] Creating ClaudeSDKClient with model: {model}")
        self.client = ClaudeSDKClient(options=options)
        self.connected = False
        logger.warning("[SERVICE] ClaudeSDKClient initialized")

    async def _ensure_connected(self):
        """Ensure client is connected."""
        logger.warning("[SERVICE] _ensure_connected called")
        if not self.connected:
            logger.warning("[SERVICE] Not connected, calling client.connect()...")
            await self.client.connect()
            logger.warning("[SERVICE] client.connect() completed")
            self.connected = True
            logger.warning("[SERVICE] Connected flag set to True")

    async def stream_brainstorm_message(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream a brainstorm response from Claude.

        Args:
            messages: Conversation history with role and content

        Yields:
            Text chunks from Claude's response
        """
        logger.warning("[BRAINSTORM] ⚡ stream_brainstorm_message CALLED")
        try:
            # Ensure client is connected
            logger.warning("[BRAINSTORM] Ensuring client is connected")
            await self._ensure_connected()
            logger.warning("[BRAINSTORM] Client connected successfully")

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
            logger.warning(f"[BRAINSTORM] Built prompt with {len(messages)} messages, length: {len(prompt)} chars")

            # Send query (non-blocking)
            logger.warning("[BRAINSTORM] 📤 Sending query to Claude API...")
            await self.client.query(prompt)
            logger.warning("[BRAINSTORM] ✅ Query sent, receiving messages...")

            # Receive messages in streaming mode
            message_count = 0
            logger.warning("[BRAINSTORM] 🔄 Starting to iterate over receive_messages()...")
            async for message in self.client.receive_messages():
                message_count += 1
                message_type = type(message).__name__
                logger.warning(f"[BRAINSTORM] 📨 Received message #{message_count}, type: {message_type}")

                # Check if this is the final ResultMessage - break out of loop
                if message_type == 'ResultMessage':
                    logger.warning(f"[BRAINSTORM] 🏁 Received ResultMessage - stream complete, breaking loop")
                    break

                # Extract text from different message types
                text_extracted = False
                if hasattr(message, 'content'):
                    if isinstance(message.content, str):
                        logger.warning(f"[BRAINSTORM] ✍️  Yielding string content, length: {len(message.content)}")
                        yield message.content
                        text_extracted = True
                    elif isinstance(message.content, list):
                        # Handle content blocks
                        for block in message.content:
                            if hasattr(block, 'text'):
                                logger.warning(f"[BRAINSTORM] ✍️  Yielding block.text, length: {len(block.text)}")
                                yield block.text
                                text_extracted = True
                            elif isinstance(block, dict) and 'text' in block:
                                logger.warning(f"[BRAINSTORM] ✍️  Yielding dict text, length: {len(block['text'])}")
                                yield block['text']
                                text_extracted = True
                elif hasattr(message, 'text'):
                    logger.warning(f"[BRAINSTORM] ✍️  Yielding message.text, length: {len(message.text)}")
                    yield message.text
                    text_extracted = True
                elif hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                    # Stream event with delta
                    logger.warning(f"[BRAINSTORM] ✍️  Yielding delta.text, length: {len(message.delta.text)}")
                    yield message.delta.text
                    text_extracted = True

                if not text_extracted and message_type not in ['SystemMessage']:
                    logger.warning(f"[BRAINSTORM] ⚠️  No text extracted from {message_type}")

            logger.warning(f"[BRAINSTORM] ✅ Finished receiving messages, total: {message_count}")

        except Exception as e:
            logger.error(f"[BRAINSTORM] ❌ Error streaming brainstorm message: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        if self.connected:
            await self.client.disconnect()
            self.connected = False

    async def __aenter__(self) -> "BrainstormingService":
        """Async context manager entry."""
        logger.warning("[SERVICE] __aenter__ called (entering async context)")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
