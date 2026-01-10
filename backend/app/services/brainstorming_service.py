"""Service for AI-powered brainstorming with Claude Agent SDK.

Uses claude_agent_sdk which works with Claude Code credentials.
Tool calls are detected via structured output parsing (JSON format in responses).
"""
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass
from typing import AsyncGenerator, Any, TYPE_CHECKING

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions, AssistantMessage, TextBlock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentType
from app.services.tools_service import ToolsService

if TYPE_CHECKING:
    from app.services.agent_factory import AgentFactory

logger = logging.getLogger(__name__)

# Pattern to detect tool call JSON in Claude's response
TOOL_CALL_PATTERN = r'\{"tool_call":\s*"explore_codebase"[^}]+\}'


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
    """Service for brainstorming with Claude via streaming using Claude Agent SDK.

    This service uses claude_agent_sdk which works with Claude Code credentials.
    Tool calls are detected via structured output parsing - Claude outputs a
    special JSON format when it wants to use tools, and we parse and execute them.
    """

    # Tool invocation instruction to add to system prompt
    TOOL_INVOCATION_INSTRUCTION = """

## Tool Invocation Format

When you need to explore the codebase to understand existing patterns, implementations,
or architecture, output the following JSON block on its own line BEFORE your regular response:

{"tool_call": "explore_codebase", "query": "your query here", "scope": "backend", "focus": "patterns"}

Parameters:
- query: What you want to learn about the codebase (required)
- scope: "backend", "frontend", or "full" (optional, default: "full")
- focus: "patterns", "dependencies", or "architecture" (optional, default: "patterns")

Example:
{"tool_call": "explore_codebase", "query": "How is user authentication implemented?", "scope": "backend", "focus": "patterns"}

After outputting this, wait for the results before continuing your response.
The tool results will be provided to you, and you should incorporate them into your analysis.

IMPORTANT: Output ONLY the JSON on its own line when calling tools, no markdown code blocks around it.

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
This is not valid - responses MUST be JSON objects with a "blocks" array.

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
CRITICAL ERROR: No text block explaining what the user is being asked to choose.
The user sees buttons but doesn't know the question or context.
ALWAYS include a text block first explaining the question.

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
Don't use multiple interactive blocks in one response.

You have access to WebSearch and WebFetch tools for research."""

    def __init__(
        self,
        api_key: str,
        db: AsyncSession | None = None,
        agent_factory: "AgentFactory | None" = None,
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

        # Set API key in environment for Claude SDK
        os.environ['ANTHROPIC_API_KEY'] = api_key

        # Client will be created lazily when we know the system prompt
        self.client: ClaudeSDKClient | None = None
        self.connected = False
        logger.warning("[SERVICE] BrainstormingService initialized (client pending)")

        # Cache for agent config
        self._agent_config: AgentType | None = None
        self._cached_system_prompt: str | None = None

        # Conversation state for tool continuations
        self._conversation_messages: list[dict[str, Any]] = []
        self._pending_tool_result: dict[str, Any] | None = None
        self._last_assistant_content: list[dict[str, Any]] = []

    async def _load_agent_config(self) -> tuple[str, str]:
        """Load agent configuration from database.

        Returns:
            Tuple of (system_prompt, model) with tool invocation instructions appended
        """
        if self._agent_config:
            base_prompt = self._agent_config.system_prompt
            model = self._agent_config.model
            # Append tool invocation instructions
            full_prompt = base_prompt + self.TOOL_INVOCATION_INSTRUCTION
            return full_prompt, model

        if not self.db:
            logger.warning("[SERVICE] No DB session, using default system prompt")
            full_prompt = self.SYSTEM_PROMPT + self.TOOL_INVOCATION_INSTRUCTION
            return full_prompt, self.model

        result = await self.db.execute(
            select(AgentType).where(AgentType.name == self.agent_name)
        )
        agent = result.scalar_one_or_none()

        if agent:
            self._agent_config = agent
            logger.info(f"[SERVICE] Loaded agent config: {agent.name}, model={agent.model}")
            # Append tool invocation instructions to agent's system prompt
            full_prompt = agent.system_prompt + self.TOOL_INVOCATION_INSTRUCTION
            return full_prompt, agent.model

        logger.warning(f"[SERVICE] Agent '{self.agent_name}' not found, using defaults")
        full_prompt = self.SYSTEM_PROMPT + self.TOOL_INVOCATION_INSTRUCTION
        return full_prompt, self.model

    async def _ensure_client(self) -> ClaudeSDKClient:
        """Ensure client is created and connected.

        Returns:
            Connected ClaudeSDKClient instance
        """
        if self.client is None:
            # Load config to get system prompt and model
            system_prompt, model = await self._load_agent_config()
            self._cached_system_prompt = system_prompt

            # Create client with options
            options = ClaudeAgentOptions(
                model=model,
                system_prompt=system_prompt,
            )
            self.client = ClaudeSDKClient(options=options)
            logger.warning(f"[SERVICE] ClaudeSDKClient created with model={model}")

        if not self.connected:
            await self.client.connect()
            self.connected = True
            logger.warning("[SERVICE] ClaudeSDKClient connected")

        return self.client

    def _detect_tool_call(self, text: str) -> dict[str, Any] | None:
        """Detect tool call JSON in text.

        Args:
            text: Text that may contain tool call JSON

        Returns:
            Parsed tool call dict if found, None otherwise
        """
        match = re.search(TOOL_CALL_PATTERN, text)
        if match:
            try:
                tool_call = json.loads(match.group(0))
                if tool_call.get("tool_call") == "explore_codebase":
                    return tool_call
            except json.JSONDecodeError:
                logger.warning(f"[SERVICE] Failed to parse tool call JSON: {match.group(0)}")
        return None

    def _extract_tool_calls(self, text: str) -> tuple[list[dict], str]:
        """Extract tool call JSON objects from text.

        Args:
            text: Response text that may contain tool call JSON

        Returns:
            Tuple of (list of tool call dicts, cleaned text without tool calls)
        """
        tool_calls = []
        cleaned_text = text

        # Find all tool call patterns
        for match in re.finditer(TOOL_CALL_PATTERN, text):
            tool_json = match.group(0)
            try:
                tool_call = json.loads(tool_json)
                if tool_call.get("tool_call") == "explore_codebase":
                    tool_calls.append(tool_call)
                    # Remove the tool call from the text
                    cleaned_text = cleaned_text.replace(tool_json, "")
            except json.JSONDecodeError:
                logger.warning(f"[SERVICE] Failed to parse tool call JSON: {tool_json}")

        # Clean up any extra whitespace from removed tool calls
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text.strip())

        return tool_calls, cleaned_text

    async def stream_brainstorm_message(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream a brainstorm response from Claude (text only, no tool detection).

        Uses Claude Agent SDK for streaming responses.

        Args:
            messages: Conversation history with role and content

        Yields:
            Text chunks from Claude's response
        """
        logger.warning("[BRAINSTORM] stream_brainstorm_message CALLED")
        try:
            # Ensure client is ready
            client = await self._ensure_client()

            # Build conversation prompt from messages
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Assistant: {content}")

            prompt = "\n\n".join(prompt_parts)
            logger.warning(f"[BRAINSTORM] Sending prompt with {len(messages)} messages")

            # Send query and stream response
            await client.query(prompt)

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            yield block.text

            logger.warning("[BRAINSTORM] Stream complete")

        except Exception as e:
            logger.error(f"[BRAINSTORM] Error streaming: {e}", exc_info=True)
            raise

    async def stream_with_tool_detection(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a brainstorm response from Claude with tool use detection.

        Uses Claude Agent SDK for streaming. Detects tool calls by parsing
        JSON patterns in the streamed text.

        Args:
            messages: Conversation history with role and content

        Yields:
            StreamChunk objects with type "text", "tool_use", or "complete"
        """
        logger.warning("[BRAINSTORM] stream_with_tool_detection CALLED")
        try:
            # Ensure client is ready
            client = await self._ensure_client()

            # Build conversation prompt from messages
            prompt_parts = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Assistant: {content}")

            prompt = "\n\n".join(prompt_parts)

            # Store for tool continuations
            self._conversation_messages = messages.copy()

            logger.warning(f"[BRAINSTORM] Sending prompt with {len(messages)} messages")

            # Send query and stream response
            await client.query(prompt)

            # Buffer for tool call detection
            full_text = ""
            tool_detected = False
            pending_text = ""

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            text_chunk = block.text
                            full_text += text_chunk
                            pending_text += text_chunk

                            # Check for tool call in accumulated text
                            if not tool_detected:
                                tool_call = self._detect_tool_call(full_text)
                                if tool_call:
                                    tool_detected = True
                                    logger.warning(
                                        f"[BRAINSTORM] Tool call detected: {tool_call}"
                                    )

                                    # Yield tool use request
                                    yield StreamChunk(
                                        type="tool_use",
                                        tool_use=ToolUseRequest(
                                            tool_name="explore_codebase",
                                            tool_id=str(uuid.uuid4()),
                                            tool_input={
                                                "query": tool_call.get("query", ""),
                                                "scope": tool_call.get("scope", "full"),
                                                "focus": tool_call.get("focus", "patterns")
                                            }
                                        )
                                    )

                                    # Remove the tool call JSON from pending text
                                    _, clean_text = self._extract_tool_calls(pending_text)
                                    if clean_text.strip():
                                        yield StreamChunk(type="text", content=clean_text)
                                    pending_text = ""
                                    continue

                            # If no tool detected yet, yield text chunks
                            # But filter out any tool call JSON that might be present
                            if not tool_detected:
                                _, clean_chunk = self._extract_tool_calls(text_chunk)
                                if clean_chunk:
                                    yield StreamChunk(type="text", content=clean_chunk)

            # Store for potential tool result continuations
            self._last_assistant_content = [{"type": "text", "text": full_text}]

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

        Uses Claude Agent SDK to send tool results back and get
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

        try:
            # Ensure client is ready
            client = await self._ensure_client()

            # Build continuation prompt with tool result
            tool_result_str = json.dumps(tool_result, indent=2)
            continuation_prompt = f"""Tool result for explore_codebase:

{tool_result_str}

Please continue your response, incorporating this information."""

            logger.warning(
                f"[BRAINSTORM] Continuing with tool result, sending new query"
            )

            # Send continuation query
            await client.query(continuation_prompt)

            # Track for nested tool calls
            full_text = ""
            tool_detected = False

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            text_chunk = block.text
                            full_text += text_chunk

                            # Check for nested tool call
                            if not tool_detected:
                                tool_call = self._detect_tool_call(full_text)
                                if tool_call:
                                    tool_detected = True
                                    logger.warning(
                                        f"[BRAINSTORM] Nested tool call in continuation: {tool_call}"
                                    )
                                    yield StreamChunk(
                                        type="tool_use",
                                        tool_use=ToolUseRequest(
                                            tool_name="explore_codebase",
                                            tool_id=str(uuid.uuid4()),
                                            tool_input={
                                                "query": tool_call.get("query", ""),
                                                "scope": tool_call.get("scope", "full"),
                                                "focus": tool_call.get("focus", "patterns")
                                            }
                                        )
                                    )
                                    continue

                            # Yield text chunks, filtering tool call JSON
                            _, clean_chunk = self._extract_tool_calls(text_chunk)
                            if clean_chunk:
                                yield StreamChunk(type="text", content=clean_chunk)

            # Update conversation state
            self._last_assistant_content = [{"type": "text", "text": full_text}]

            yield StreamChunk(type="complete")
            logger.warning("[BRAINSTORM] Tool result continuation complete")

        except Exception as e:
            logger.error(f"[BRAINSTORM] Error in continue_with_tool_result: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the service and cleanup resources."""
        if self.client and self.connected:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warning(f"[SERVICE] Error disconnecting client: {e}")

        self.connected = False
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
