"""Service for AI-powered brainstorming with Claude Agent SDK."""
import json
import logging
import os
from dataclasses import dataclass
from typing import AsyncGenerator, Any, TYPE_CHECKING
from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions, ToolUseBlock

if TYPE_CHECKING:
    from app.services.agent_factory import AgentFactory

logger = logging.getLogger(__name__)


@dataclass
class ToolUseRequest:
    """Represents a tool use request from Claude."""

    tool_name: str
    tool_id: str
    tool_input: dict[str, Any]


@dataclass
class StreamChunk:
    """Represents a chunk of streamed content."""

    type: str  # "text", "tool_use", "complete"
    content: str | None = None
    tool_use: ToolUseRequest | None = None


class BrainstormingService:
    """Service for brainstorming with Claude via streaming using Agent SDK."""

    SYSTEM_PROMPT = """You are an AI Product Discovery facilitator helping a Product Manager define a concrete, actionable feature.

## Critical Context
The PM you're talking to:
- **Non-technical**: Never mention code, APIs, databases, frameworks, or technical implementation
- **Time-constrained**: Be concise. Get to actionable insights quickly
- **Results-oriented**: Always drive toward a concrete feature definition

## Your Mission: Produce a Feature Brief
Every conversation should progress through these phases to reach a concrete feature:

**Phase 1: Understand (1-2 questions max)**
- What user problem are we solving?
- Who specifically benefits from this?
- What's the business goal?

**Phase 2: Define (1-2 questions max)**
- What's the core value proposition?
- What's the minimum viable version?
- How will we measure success?

**Phase 3: Validate & Conclude**
- Summarize the feature concept clearly
- List success metrics
- Present a clear Feature Brief with:
  - Feature Name
  - User Problem
  - Target Users
  - Core Functionality (3-5 bullets)
  - Success Metrics (2-3 KPIs)
  - Key Risks/Considerations

## Critical Rules
1. **Stay focused**: Don't ask endless exploratory questions. Move toward concrete output.
2. **Be strategic**: Each question should uncover critical information needed for the brief
3. **Synthesize often**: After 2-3 exchanges, summarize what you know and ask what's missing
4. **Drive to conclusion**: After 4-6 exchanges, you should have enough to present a Feature Brief
5. **No technical talk**: Focus on WHAT the feature does, not HOW it's built
6. **Be opinionated**: Suggest specific feature scopes, metrics, and priorities based on best practices

## Conversation Flow Example
1. User: "I want authentication"
2. You: "Let's define the authentication feature. First, who are the primary users?" + (button group: Social Login / Email / Enterprise SSO)
3. User: Selects options
4. You: "Great! Now, what aspects are most important for this authentication?" + (multi-select: Security / UX / Speed)
5. User: Selects priorities
6. You: **Present Feature Brief** with text summarizing everything + clear definition, scope, metrics, and next steps

**REMEMBER**: Every response with buttons/multi-select MUST have explanatory text first.

**ALWAYS aim to conclude with a concrete Feature Brief within 5-7 exchanges.**

# Response Format

You MUST respond with a JSON object containing a "blocks" array. Each response should be:
```json
{
  "blocks": [
    // array of block objects here
  ]
}
```

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

**CRITICAL RULE: ALWAYS start with a text block explaining the question or context.**

1. **Response Structure**: Every response MUST be a JSON object with a "blocks" array
2. **Text First (MANDATORY)**: ALWAYS start with a text block that:
   - Explains what you're asking or why
   - Provides context for the interactive element
   - Is written as a clear question or statement
   - NEVER present buttons/options without explaining what they're for
3. **One Interactive Block**: Use only ONE button_group OR multi_select per response
4. **Button vs Multi-Select**:
   - Use button_group for mutually exclusive actions
   - Use multi_select when users can choose multiple items
5. **Progressive Disclosure**: Don't overwhelm users - break complex flows into steps

## Examples

### Good: Text + Button Group
```json
{
  "blocks": [
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
}
```

### Good: Text + Multi-Select
```json
{
  "blocks": [
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
}
```

### Bad: Plain Text (Missing JSON Structure)
```
I can help you explore this feature. What would you like to focus on?
```
❌ This is not valid - responses MUST be JSON objects with a "blocks" array.

### Bad: Interactive Block Without Context Text
```json
{
  "blocks": [
    {
      "type": "button_group",
      "buttons": [
        {"id": "consumers", "label": "Consumers (B2C)", "action": "Target consumers"},
        {"id": "business", "label": "Business Users (B2B)", "action": "Target businesses"}
      ]
    }
  ]
}
```
❌ CRITICAL ERROR: No text block explaining what the user is being asked to choose.
❌ The user sees buttons but doesn't know the question or context.
❌ ALWAYS include a text block first explaining the question.

### Bad: Too Many Interactive Elements
```json
{
  "blocks": [
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
}
```
❌ Don't use multiple interactive blocks in one response.

You have access to WebSearch and WebFetch tools for research."""

    def __init__(
        self,
        api_key: str,
        agent_factory: "AgentFactory | None" = None,  # noqa: F821
        agent_name: str = "brainstorm",
        model: str = "claude-sonnet-4-5"
    ) -> None:
        """Initialize the brainstorming service.

        Args:
            api_key: Anthropic API key
            agent_factory: Optional AgentFactory for dynamic tool loading
            agent_name: Agent type name to use (default: "brainstorm")
            model: Claude model to use (fallback if no agent_factory)
        """
        logger.warning("[SERVICE] __init__ called")
        self.api_key = api_key
        self.agent_factory = agent_factory
        self.agent_name = agent_name
        self.model = model
        self.client = None
        self.connected = False

        # Set API key in environment for Claude SDK
        os.environ['ANTHROPIC_API_KEY'] = api_key
        logger.warning("[SERVICE] API key set in environment")

    async def _ensure_connected(self):
        """Ensure client is connected."""
        logger.warning("[SERVICE] _ensure_connected called")
        if not self.connected:
            logger.warning("[SERVICE] Not connected, initializing client...")

            if self.agent_factory:
                # Use agent factory to create client with dynamic tools
                logger.warning(f"[SERVICE] Creating client via AgentFactory for agent '{self.agent_name}'")
                self.client = await self.agent_factory.create_agent_client(self.agent_name)
            else:
                # Fallback: Create client with static config (backwards compatibility)
                logger.warning("[SERVICE] Creating client with static config (no AgentFactory)")
                options = ClaudeAgentOptions(
                    model=self.model,
                    system_prompt=self.SYSTEM_PROMPT,
                )
                self.client = ClaudeSDKClient(options=options)

            logger.warning("[SERVICE] Calling client.connect()...")
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
                    logger.warning("[BRAINSTORM] 🏁 Received ResultMessage - stream complete, breaking loop")
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

    async def stream_with_tool_detection(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a brainstorm response from Claude with tool use detection.

        This method is similar to stream_brainstorm_message but returns structured
        StreamChunk objects that can indicate tool_use requests from Claude.

        Args:
            messages: Conversation history with role and content

        Yields:
            StreamChunk objects with type "text", "tool_use", or "complete"
        """
        logger.warning("[BRAINSTORM] stream_with_tool_detection CALLED")
        try:
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
            logger.warning(f"[BRAINSTORM] Built prompt with {len(messages)} messages")

            # Send query
            logger.warning("[BRAINSTORM] Sending query to Claude API...")
            await self.client.query(prompt)
            logger.warning("[BRAINSTORM] Query sent, receiving messages...")

            # Receive messages
            message_count = 0
            async for message in self.client.receive_messages():
                message_count += 1
                message_type = type(message).__name__
                logger.warning(f"[BRAINSTORM] Received message #{message_count}, type: {message_type}")

                # Check for ResultMessage - stream complete
                if message_type == 'ResultMessage':
                    logger.warning("[BRAINSTORM] ResultMessage - stream complete")
                    yield StreamChunk(type="complete")
                    break

                # Process content blocks
                if hasattr(message, 'content'):
                    if isinstance(message.content, list):
                        for block in message.content:
                            # Check for ToolUseBlock
                            if isinstance(block, ToolUseBlock):
                                logger.warning(
                                    f"[BRAINSTORM] ToolUseBlock detected: "
                                    f"name={block.name}, id={block.id}"
                                )
                                yield StreamChunk(
                                    type="tool_use",
                                    tool_use=ToolUseRequest(
                                        tool_name=block.name,
                                        tool_id=block.id,
                                        tool_input=block.input
                                    )
                                )
                            # Check for text content
                            elif hasattr(block, 'text'):
                                yield StreamChunk(type="text", content=block.text)
                            elif isinstance(block, dict):
                                if 'text' in block:
                                    yield StreamChunk(type="text", content=block['text'])
                                elif block.get('type') == 'tool_use':
                                    # Handle dict-based tool_use
                                    logger.warning(
                                        f"[BRAINSTORM] Dict tool_use detected: {block}"
                                    )
                                    yield StreamChunk(
                                        type="tool_use",
                                        tool_use=ToolUseRequest(
                                            tool_name=block.get('name', ''),
                                            tool_id=block.get('id', ''),
                                            tool_input=block.get('input', {})
                                        )
                                    )
                    elif isinstance(message.content, str):
                        yield StreamChunk(type="text", content=message.content)

                # Handle other text attributes
                elif hasattr(message, 'text'):
                    yield StreamChunk(type="text", content=message.text)
                elif hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                    yield StreamChunk(type="text", content=message.delta.text)

            logger.warning(f"[BRAINSTORM] Finished, total messages: {message_count}")

        except Exception as e:
            logger.error(f"[BRAINSTORM] Error in stream_with_tool_detection: {e}", exc_info=True)
            raise

    async def continue_with_tool_result(
        self,
        tool_id: str,
        tool_result: dict[str, Any]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Continue the conversation after a tool has been executed.

        Args:
            tool_id: The ID of the tool that was executed
            tool_result: The result from the tool execution

        Yields:
            StreamChunk objects with Claude's continued response
        """
        logger.warning(f"[BRAINSTORM] continue_with_tool_result called for tool_id={tool_id}")

        if not self.connected or not self.client:
            raise RuntimeError("Client not connected. Call stream_with_tool_detection first.")

        # Format the tool result as a user message that Claude can understand
        tool_result_prompt = f"""Tool result for explore_codebase (id={tool_id}):

{json.dumps(tool_result, indent=2)}

Based on this codebase exploration, please provide your analysis and continue the conversation with the PM. Remember to format your response as JSON with a "blocks" array."""

        # Send the tool result as a continuation
        logger.warning("[BRAINSTORM] Sending tool result to Claude...")
        await self.client.query(tool_result_prompt)

        # Receive Claude's response
        async for message in self.client.receive_messages():
            message_type = type(message).__name__
            logger.warning(f"[BRAINSTORM] Tool result response, type: {message_type}")

            if message_type == 'ResultMessage':
                yield StreamChunk(type="complete")
                break

            if hasattr(message, 'content'):
                if isinstance(message.content, list):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            yield StreamChunk(
                                type="tool_use",
                                tool_use=ToolUseRequest(
                                    tool_name=block.name,
                                    tool_id=block.id,
                                    tool_input=block.input
                                )
                            )
                        elif hasattr(block, 'text'):
                            yield StreamChunk(type="text", content=block.text)
                        elif isinstance(block, dict) and 'text' in block:
                            yield StreamChunk(type="text", content=block['text'])
                elif isinstance(message.content, str):
                    yield StreamChunk(type="text", content=message.content)
            elif hasattr(message, 'text'):
                yield StreamChunk(type="text", content=message.text)
            elif hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                yield StreamChunk(type="text", content=message.delta.text)

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
