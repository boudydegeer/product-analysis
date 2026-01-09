"""Service for AI-powered brainstorming with direct Anthropic API (tools support)."""
import json
import logging
import os
from dataclasses import dataclass
from typing import AsyncGenerator, Any, TYPE_CHECKING

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentType
from app.services.tools_service import ToolsService

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
    """Service for brainstorming with Claude via streaming using direct Anthropic API.

    This service uses the direct Anthropic API instead of Claude Agent SDK
    to support custom tool definitions with full input schemas.
    """

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
        db: AsyncSession | None = None,
        agent_factory: "AgentFactory | None" = None,  # noqa: F821
        agent_name: str = "brainstorm",
        model: str = "claude-sonnet-4-20250514"
    ) -> None:
        """Initialize the brainstorming service.

        Args:
            api_key: Anthropic API key
            db: Database session for loading tools and agent config
            agent_factory: Optional AgentFactory for dynamic tool loading (legacy)
            agent_name: Agent type name to use (default: "brainstorm")
            model: Claude model to use (fallback if no agent config)
        """
        logger.warning("[SERVICE] __init__ called")
        self.api_key = api_key
        self.db = db
        self.agent_factory = agent_factory
        self.agent_name = agent_name
        self.model = model

        # Create Anthropic client
        self.client = AsyncAnthropic(api_key=api_key)
        logger.warning("[SERVICE] AsyncAnthropic client initialized")

        # Cache for agent config and tools
        self._agent_config: AgentType | None = None
        self._tools: list[dict[str, Any]] | None = None

        # Conversation state for tool continuations
        self._conversation_messages: list[dict[str, Any]] = []
        self._last_assistant_content: list[dict[str, Any]] = []

    async def _load_agent_config(self) -> tuple[str, str]:
        """Load agent configuration from database.

        Returns:
            Tuple of (system_prompt, model)
        """
        if self._agent_config:
            return self._agent_config.system_prompt, self._agent_config.model

        if not self.db:
            logger.warning("[SERVICE] No DB session, using default system prompt")
            return self.SYSTEM_PROMPT, self.model

        result = await self.db.execute(
            select(AgentType).where(AgentType.name == self.agent_name)
        )
        agent = result.scalar_one_or_none()

        if agent:
            self._agent_config = agent
            logger.info(f"[SERVICE] Loaded agent config: {agent.name}, model={agent.model}")
            return agent.system_prompt, agent.model

        logger.warning(f"[SERVICE] Agent '{self.agent_name}' not found, using defaults")
        return self.SYSTEM_PROMPT, self.model

    async def _load_tools(self) -> list[dict[str, Any]]:
        """Load tools for this agent from database.

        Returns:
            List of tool definitions in Anthropic API format
        """
        if self._tools is not None:
            return self._tools

        if not self.db:
            logger.warning("[SERVICE] No DB session, no tools available")
            self._tools = []
            return self._tools

        # Get agent config first
        system_prompt, _ = await self._load_agent_config()

        if not self._agent_config:
            logger.warning("[SERVICE] No agent config, no tools available")
            self._tools = []
            return self._tools

        # Load tools from database
        tools_service = ToolsService(self.db)
        db_tools = await tools_service.get_tools_for_agent(
            self._agent_config.id,
            enabled_only=True
        )

        # Convert to Anthropic API format
        anthropic_tools = []
        for tool in db_tools:
            # Tool definition should contain input_schema
            definition = tool.get("definition", {}) if isinstance(tool, dict) else {}

            if "input_schema" in definition:
                anthropic_tool = {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "input_schema": definition["input_schema"]
                }
                anthropic_tools.append(anthropic_tool)
                logger.info(f"[SERVICE] Loaded tool: {tool['name']}")
            else:
                logger.warning(
                    f"[SERVICE] Tool '{tool.get('name', 'unknown')}' missing input_schema, skipped"
                )

        self._tools = anthropic_tools
        logger.info(f"[SERVICE] Loaded {len(anthropic_tools)} tools for agent '{self.agent_name}'")
        return self._tools

    async def stream_brainstorm_message(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream a brainstorm response from Claude (text only, no tool detection).

        Args:
            messages: Conversation history with role and content

        Yields:
            Text chunks from Claude's response
        """
        logger.warning("[BRAINSTORM] stream_brainstorm_message CALLED")
        try:
            # Load configuration
            system_prompt, model = await self._load_agent_config()

            # Convert messages to Anthropic format
            api_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]

            logger.warning(f"[BRAINSTORM] Sending to {model} with {len(api_messages)} messages")

            # Stream response using direct Anthropic API
            async with self.client.messages.stream(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=api_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.warning("[BRAINSTORM] Stream complete")

        except Exception as e:
            logger.error(f"[BRAINSTORM] Error streaming: {e}", exc_info=True)
            raise

    async def stream_with_tool_detection(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a brainstorm response from Claude with tool use detection.

        Uses the direct Anthropic API with full tool definitions (input schemas).
        Properly handles streaming events including tool_use blocks with
        input accumulation from delta events.

        Args:
            messages: Conversation history with role and content

        Yields:
            StreamChunk objects with type "text", "tool_use", or "complete"
        """
        logger.warning("[BRAINSTORM] stream_with_tool_detection CALLED")
        try:
            # Load configuration and tools
            system_prompt, model = await self._load_agent_config()
            tools = await self._load_tools()

            # Convert messages to Anthropic format
            api_messages = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in messages
            ]

            # Store for tool continuations
            self._conversation_messages = api_messages.copy()

            logger.warning(
                f"[BRAINSTORM] Sending to {model} with {len(api_messages)} messages "
                f"and {len(tools)} tools"
            )

            # Build request kwargs
            request_kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": api_messages,
            }
            if tools:
                request_kwargs["tools"] = tools

            # Track current tool use block being streamed
            current_tool_id: str | None = None
            current_tool_name: str | None = None
            current_tool_input_json: str = ""

            # Track all content blocks for conversation continuity
            assistant_content_blocks: list[dict[str, Any]] = []

            # Stream response using direct Anthropic API
            async with self.client.messages.stream(**request_kwargs) as stream:
                async for event in stream:
                    event_type = event.type

                    if event_type == "content_block_start":
                        # New content block starting
                        block = event.content_block
                        if block.type == "text":
                            # Text block - nothing special to do on start
                            pass
                        elif block.type == "tool_use":
                            # Tool use block starting
                            current_tool_id = block.id
                            current_tool_name = block.name
                            current_tool_input_json = ""
                            logger.warning(
                                f"[BRAINSTORM] Tool use block started: "
                                f"name={current_tool_name}, id={current_tool_id}"
                            )

                    elif event_type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            # Text content delta
                            yield StreamChunk(type="text", content=delta.text)
                        elif delta.type == "input_json_delta":
                            # Tool input JSON delta - accumulate
                            current_tool_input_json += delta.partial_json

                    elif event_type == "content_block_stop":
                        # Content block finished
                        if current_tool_id and current_tool_name:
                            # Parse accumulated JSON input
                            try:
                                tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                            except json.JSONDecodeError:
                                logger.error(
                                    f"[BRAINSTORM] Failed to parse tool input JSON: "
                                    f"{current_tool_input_json[:200]}"
                                )
                                tool_input = {}

                            logger.warning(
                                f"[BRAINSTORM] Tool use complete: name={current_tool_name}, "
                                f"id={current_tool_id}, input={tool_input}"
                            )

                            # Store tool use block for continuation
                            assistant_content_blocks.append({
                                "type": "tool_use",
                                "id": current_tool_id,
                                "name": current_tool_name,
                                "input": tool_input
                            })

                            # Yield the tool use request
                            yield StreamChunk(
                                type="tool_use",
                                tool_use=ToolUseRequest(
                                    tool_name=current_tool_name,
                                    tool_id=current_tool_id,
                                    tool_input=tool_input
                                )
                            )

                            # Reset tool tracking
                            current_tool_id = None
                            current_tool_name = None
                            current_tool_input_json = ""

                    elif event_type == "message_stop":
                        # Message complete
                        logger.warning("[BRAINSTORM] Message stop event received")

            # Store assistant content for potential tool continuations
            self._last_assistant_content = assistant_content_blocks

            yield StreamChunk(type="complete")
            logger.warning("[BRAINSTORM] Stream complete")

        except Exception as e:
            logger.error(f"[BRAINSTORM] Error in stream_with_tool_detection: {e}", exc_info=True)
            raise

    async def continue_with_tool_result(
        self,
        tool_id: str,
        tool_result: dict[str, Any]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Continue the conversation after a tool has been executed.

        Uses the direct Anthropic API to send tool results back and get
        Claude's continued response.

        Args:
            tool_id: The ID of the tool that was executed
            tool_result: The result from the tool execution

        Yields:
            StreamChunk objects with Claude's continued response
        """
        logger.warning(f"[BRAINSTORM] continue_with_tool_result called for tool_id={tool_id}")

        if not self._conversation_messages:
            raise RuntimeError(
                "No conversation context. Call stream_with_tool_detection first."
            )

        # Load configuration and tools
        system_prompt, model = await self._load_agent_config()
        tools = await self._load_tools()

        # Build the continuation messages:
        # 1. Original conversation
        # 2. Assistant's response with tool_use
        # 3. User's tool_result
        continuation_messages = self._conversation_messages.copy()

        # Add assistant message with tool_use content
        if self._last_assistant_content:
            continuation_messages.append({
                "role": "assistant",
                "content": self._last_assistant_content
            })

        # Add tool result as user message
        continuation_messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(tool_result)
            }]
        })

        logger.warning(
            f"[BRAINSTORM] Continuing with tool result, "
            f"{len(continuation_messages)} messages total"
        )

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": continuation_messages,
        }
        if tools:
            request_kwargs["tools"] = tools

        # Track current tool use block being streamed
        current_tool_id: str | None = None
        current_tool_name: str | None = None
        current_tool_input_json: str = ""

        # Track content blocks for potential nested tool calls
        assistant_content_blocks: list[dict[str, Any]] = []

        # Stream response
        async with self.client.messages.stream(**request_kwargs) as stream:
            async for event in stream:
                event_type = event.type

                if event_type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_id = block.id
                        current_tool_name = block.name
                        current_tool_input_json = ""
                        logger.warning(
                            f"[BRAINSTORM] Tool use block started in continuation: "
                            f"name={current_tool_name}, id={current_tool_id}"
                        )

                elif event_type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield StreamChunk(type="text", content=delta.text)
                    elif delta.type == "input_json_delta":
                        current_tool_input_json += delta.partial_json

                elif event_type == "content_block_stop":
                    if current_tool_id and current_tool_name:
                        try:
                            tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
                        except json.JSONDecodeError:
                            tool_input = {}

                        logger.warning(
                            f"[BRAINSTORM] Tool use in continuation: "
                            f"name={current_tool_name}, id={current_tool_id}"
                        )

                        assistant_content_blocks.append({
                            "type": "tool_use",
                            "id": current_tool_id,
                            "name": current_tool_name,
                            "input": tool_input
                        })

                        yield StreamChunk(
                            type="tool_use",
                            tool_use=ToolUseRequest(
                                tool_name=current_tool_name,
                                tool_id=current_tool_id,
                                tool_input=tool_input
                            )
                        )

                        current_tool_id = None
                        current_tool_name = None
                        current_tool_input_json = ""

                elif event_type == "message_stop":
                    logger.warning("[BRAINSTORM] Continuation message stop")

        # Update conversation state for potential further continuations
        self._conversation_messages = continuation_messages
        self._last_assistant_content = assistant_content_blocks

        yield StreamChunk(type="complete")
        logger.warning("[BRAINSTORM] Tool result continuation complete")

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        # AsyncAnthropic client doesn't require explicit cleanup
        # Reset conversation state
        self._conversation_messages = []
        self._last_assistant_content = []
        logger.warning("[SERVICE] Closed and reset conversation state")

    async def __aenter__(self) -> "BrainstormingService":
        """Async context manager entry."""
        logger.warning("[SERVICE] __aenter__ called (entering async context)")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
