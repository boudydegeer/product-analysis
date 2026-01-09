# Codebase Exploration Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Enable agents to explore the codebase via GitHub Actions workflow using Claude Agent SDK, providing technical context without direct repository access from backend.

**Architecture:** Reuses existing Feature Analysis infrastructure (GitHubService, polling/webhook). Agents invoke `explore_codebase` tool → triggers GitHub workflow → Claude SDK explores repo with Read/Glob/Grep → results returned as artifact → injected back into agent conversation. Frontend shows "🧐 Investigating..." while waiting.

**Tech Stack:** FastAPI, SQLAlchemy, GitHub Actions, Claude Agent SDK, Vue 3, TypeScript, existing GitHubService

**Dependencies:** Requires Dynamic Tools System (2026-01-09-dynamic-tools-system.md) to be implemented first.

---

## Phase 1: Tool Definition & Database

### Task 1: Register explore_codebase Tool

**Files:**
- Create: `backend/scripts/seed_explore_codebase_tool.py`

**Step 1: Write test for tool registration**

Create: `backend/tests/scripts/test_seed_explore_codebase_tool.py`

```python
"""Tests for explore_codebase tool seeding."""
import pytest
from app.models.tool import Tool
from sqlalchemy import select


@pytest.mark.asyncio
async def test_seed_creates_tool(db_session):
    """Test that seed script creates explore_codebase tool."""
    from scripts.seed_explore_codebase_tool import seed_explore_codebase_tool

    await seed_explore_codebase_tool(db_session)

    result = await db_session.execute(
        select(Tool).where(Tool.name == "explore_codebase")
    )
    tool = result.scalar_one_or_none()

    assert tool is not None
    assert tool.name == "explore_codebase"
    assert tool.category == "code"
    assert tool.tool_type == "custom"
    assert "query" in tool.definition["input_schema"]["properties"]
    assert "scope" in tool.definition["input_schema"]["properties"]
    assert tool.is_dangerous is False


@pytest.mark.asyncio
async def test_seed_is_idempotent(db_session):
    """Test that running seed twice doesn't create duplicates."""
    from scripts.seed_explore_codebase_tool import seed_explore_codebase_tool

    await seed_explore_codebase_tool(db_session)
    await seed_explore_codebase_tool(db_session)  # Run again

    result = await db_session.execute(
        select(Tool).where(Tool.name == "explore_codebase")
    )
    tools = result.scalars().all()

    assert len(tools) == 1  # Only one tool created
```

**Step 2: Run test to verify it fails**

```bash
cd backend
poetry run pytest tests/scripts/test_seed_explore_codebase_tool.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.seed_explore_codebase_tool'"

**Step 3: Create seed script**

Create: `backend/scripts/seed_explore_codebase_tool.py`

```python
"""Seed script for explore_codebase tool."""
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_explore_codebase_tool(db: AsyncSession) -> Tool:
    """Seed the explore_codebase tool.

    Returns:
        Created or existing Tool instance
    """
    logger.info("Seeding explore_codebase tool...")

    # Check if already exists
    result = await db.execute(
        select(Tool).where(Tool.name == "explore_codebase")
    )
    existing_tool = result.scalar_one_or_none()

    if existing_tool:
        logger.info("Tool 'explore_codebase' already exists, skipping")
        return existing_tool

    tool_data = {
        "name": "explore_codebase",
        "description": "Explore the codebase to understand existing implementation, find patterns, or locate relevant code. Use when you need technical context about how something is implemented.",
        "category": "code",
        "tool_type": "custom",
        "definition": {
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to investigate (e.g., 'how authentication works', 'list all API endpoints', 'find user model definition')"
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["backend", "frontend", "full"],
                        "default": "full",
                        "description": "Which part of codebase to explore: backend (Python/FastAPI), frontend (Vue/TypeScript), or full (entire repo)"
                    },
                    "focus": {
                        "type": "string",
                        "enum": ["files", "patterns", "architecture", "dependencies"],
                        "default": "patterns",
                        "description": "What aspect to focus on: files (file structure), patterns (code patterns), architecture (how components relate), dependencies (imports/relationships)"
                    }
                },
                "required": ["query"]
            }
        },
        "is_dangerous": False,
        "requires_approval": False,
        "tags": ["codebase", "exploration", "context"],
        "example_usage": "explore_codebase(query='how does authentication work', scope='backend', focus='architecture')",
        "version": "1.0.0",
    }

    tool = Tool(**tool_data)
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    logger.info(f"Created tool: {tool.name} (id={tool.id})")
    return tool


async def assign_to_brainstorm_agent(db: AsyncSession, tool: Tool) -> None:
    """Assign explore_codebase to brainstorm agent."""
    logger.info("Assigning explore_codebase to brainstorm agent...")

    # Get brainstorm agent
    result = await db.execute(
        select(AgentType).where(AgentType.name == "brainstorm")
    )
    agent = result.scalar_one_or_none()

    if not agent:
        logger.warning("Brainstorm agent not found, skipping assignment")
        return

    # Check if already assigned
    result = await db.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == agent.id,
            AgentToolConfig.tool_id == tool.id
        )
    )
    existing_config = result.scalar_one_or_none()

    if existing_config:
        logger.info("Tool already assigned to brainstorm agent, skipping")
        return

    # Assign with order_index after existing tools
    result = await db.execute(
        select(AgentToolConfig)
        .where(AgentToolConfig.agent_type_id == agent.id)
        .order_by(AgentToolConfig.order_index.desc())
    )
    last_config = result.first()
    next_order = (last_config[0].order_index + 1) if last_config else 1

    config = AgentToolConfig(
        agent_type_id=agent.id,
        tool_id=tool.id,
        enabled_for_agent=True,
        order_index=next_order,
        allow_use=True,
        usage_limit=10,  # Max 10 explorations per session
    )
    db.add(config)
    await db.commit()

    logger.info(f"Assigned tool to brainstorm agent (order={next_order})")


async def main():
    """Main seeding function."""
    logger.info("Starting explore_codebase tool seeding...")

    async with async_session_maker() as db:
        tool = await seed_explore_codebase_tool(db)
        await assign_to_brainstorm_agent(db, tool)

    logger.info("Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest tests/scripts/test_seed_explore_codebase_tool.py -v
```

Expected: PASS - All tests pass

**Step 5: Run seed script**

```bash
poetry run python scripts/seed_explore_codebase_tool.py
```

Expected: SUCCESS - Tool created and assigned to brainstorm agent

**Step 6: Verify in database**

```bash
docker exec -it postgres-dev psql -U postgres -d product_analysis -c "SELECT name, category, tool_type FROM tools WHERE name='explore_codebase';"
```

Expected: See explore_codebase tool

**Step 7: Commit**

```bash
git add backend/scripts/seed_explore_codebase_tool.py backend/tests/scripts/test_seed_explore_codebase_tool.py
git commit -m "feat: add explore_codebase tool definition

- Add tool with query, scope, and focus parameters
- Assign to brainstorm agent with usage limit
- Add idempotent seed script
- Add comprehensive tests"
```

---

## Phase 2: GitHub Workflow & Exploration Script

### Task 2: Create GitHub Workflow for Codebase Exploration

**Files:**
- Create: `.github/workflows/explore-codebase.yml`

**Step 1: Create workflow file**

Create: `.github/workflows/explore-codebase.yml`

```yaml
name: Explore Codebase

on:
  workflow_dispatch:
    inputs:
      exploration_id:
        description: 'Unique ID for this exploration'
        required: true
        type: string
      query:
        description: 'What to explore in the codebase'
        required: true
        type: string
      scope:
        description: 'Scope of exploration'
        required: false
        type: choice
        options:
          - full
          - backend
          - frontend
        default: 'full'
      focus:
        description: 'What to focus on'
        required: false
        type: choice
        options:
          - patterns
          - files
          - architecture
          - dependencies
        default: 'patterns'
      callback_url:
        description: 'Webhook URL for results (optional)'
        required: false
        type: string

jobs:
  explore:
    runs-on: ubuntu-latest
    timeout-minutes: 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Claude Agent SDK
        run: |
          pip install claude-agent-sdk anthropic

      - name: Explore Codebase
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          EXPLORATION_ID: ${{ github.event.inputs.exploration_id }}
          QUERY: ${{ github.event.inputs.query }}
          SCOPE: ${{ github.event.inputs.scope }}
          FOCUS: ${{ github.event.inputs.focus }}
        run: |
          python .github/scripts/explore_codebase.py

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: exploration-${{ github.event.inputs.exploration_id }}
          path: exploration_results.json
          retention-days: 1

      - name: Send Webhook (if provided)
        if: github.event.inputs.callback_url != ''
        run: |
          if [ -f exploration_results.json ]; then
            curl -X POST "${{ github.event.inputs.callback_url }}" \
              -H "Content-Type: application/json" \
              -H "X-GitHub-Event: codebase-exploration" \
              -H "X-Exploration-ID: ${{ github.event.inputs.exploration_id }}" \
              -d @exploration_results.json
          fi
```

**Step 2: Commit workflow**

```bash
git add .github/workflows/explore-codebase.yml
git commit -m "feat: add GitHub workflow for codebase exploration

- Accept query, scope, focus parameters
- Run exploration with Claude Agent SDK
- Upload results as artifact
- Send webhook notification if URL provided
- 5 minute timeout for safety"
```

---

### Task 3: Create Exploration Script

**Files:**
- Create: `.github/scripts/explore_codebase.py`

**Step 1: Create exploration script**

Create: `.github/scripts/explore_codebase.py`

```python
"""Script to explore codebase using Claude Agent SDK."""
import os
import json
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for required environment variables
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

EXPLORATION_ID = os.environ.get("EXPLORATION_ID", "unknown")
QUERY = os.environ.get("QUERY", "")
SCOPE = os.environ.get("SCOPE", "full")
FOCUS = os.environ.get("FOCUS", "patterns")

# System prompt for codebase exploration
SYSTEM_PROMPT = """You are a codebase explorer assistant. Your job is to investigate codebases and provide clear, structured summaries.

## Your Tools

You have access to:
- **Glob**: Find files by pattern (e.g., "**/*.py", "src/**/*.ts")
- **Grep**: Search for code patterns (regex supported)
- **Read**: Read file contents
- **Bash**: Run git commands (git log, git blame, etc.)

## Exploration Strategy

1. **Understand the query**: What is the user asking?
2. **Find relevant files**: Use Glob to locate files
3. **Search for patterns**: Use Grep to find specific code
4. **Read key files**: Use Read to examine implementations
5. **Synthesize findings**: Combine information into clear structure

## Output Format

You MUST respond with ONLY a JSON object (no markdown, no extra text):

{
  "exploration_id": "the exploration ID",
  "query": "original query",
  "summary": "2-3 sentence overview of what you found",
  "relevant_files": [
    {
      "path": "file/path",
      "purpose": "what this file does",
      "importance": "high|medium|low"
    }
  ],
  "key_patterns": [
    {
      "pattern": "pattern name or description",
      "details": "explanation",
      "examples": ["example1", "example2"]
    }
  ],
  "code_examples": [
    {
      "file": "file/path",
      "lines": "10-25",
      "snippet": "actual code snippet",
      "explanation": "why this is relevant"
    }
  ],
  "architecture_notes": "How components relate, dependencies, design patterns used",
  "recommendations": ["recommendation1", "recommendation2"],
  "confidence": "high|medium|low"
}

## Important Rules

1. **Be specific**: Provide exact file paths, line numbers, function names
2. **Be concise**: Focus on what's directly relevant to the query
3. **Prioritize**: Show most important findings first
4. **Be accurate**: Only include information you actually found
5. **Output pure JSON**: No markdown code blocks, no extra text
"""


async def explore_codebase():
    """Execute codebase exploration."""
    logger.info(f"Starting exploration: {EXPLORATION_ID}")
    logger.info(f"Query: {QUERY}")
    logger.info(f"Scope: {SCOPE}")
    logger.info(f"Focus: {FOCUS}")

    try:
        from claude_agent_sdk import ClaudeSDKClient
        from claude_agent_sdk.types import ClaudeAgentOptions

        # Determine search paths based on scope
        search_paths = {
            "backend": "backend/",
            "frontend": "frontend/",
            "full": "./"
        }
        base_path = search_paths.get(SCOPE, "./")

        # Build context-aware prompt based on focus
        focus_instructions = {
            "files": "Focus on finding and categorizing relevant files. List file structures and purposes.",
            "patterns": "Focus on identifying code patterns, design patterns, and common approaches used.",
            "architecture": "Focus on how components relate to each other, dependencies, and overall architecture.",
            "dependencies": "Focus on imports, relationships between modules, and dependency chains."
        }
        focus_instruction = focus_instructions.get(FOCUS, "")

        # Initialize Claude SDK
        options = ClaudeAgentOptions(
            model="claude-sonnet-4-5",
            system_prompt=SYSTEM_PROMPT,
        )

        client = ClaudeSDKClient(options=options)
        await client.connect()
        logger.info("Connected to Claude SDK")

        # Build exploration prompt
        prompt = f"""Explore the codebase in '{base_path}' to answer this query:

**Query**: {QUERY}

**Scope**: {SCOPE} (search in: {base_path})

**Focus**: {FOCUS}
{focus_instruction}

**Exploration ID**: {EXPLORATION_ID}

Provide a structured JSON response with your findings. Remember to output ONLY the JSON object, no other text."""

        # Execute exploration
        await client.query(prompt)
        logger.info("Query sent, receiving messages...")

        full_response = ""
        async for message in client.receive_messages():
            message_type = type(message).__name__
            logger.info(f"Received message type: {message_type}")

            if message_type == 'ResultMessage':
                logger.info("Received ResultMessage, exploration complete")
                break

            # Extract text from message
            if hasattr(message, 'content'):
                if isinstance(message.content, str):
                    full_response += message.content
                elif isinstance(message.content, list):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            full_response += block.text
                        elif isinstance(block, dict) and 'text' in block:
                            full_response += block['text']
            elif hasattr(message, 'text'):
                full_response += message.text
            elif hasattr(message, 'delta') and hasattr(message.delta, 'text'):
                full_response += message.delta.text

        await client.disconnect()
        logger.info("Disconnected from Claude SDK")

        # Parse results
        logger.info(f"Received response length: {len(full_response)} chars")

        # Try to extract JSON from response
        results = None
        try:
            # Try direct JSON parse
            results = json.loads(full_response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', full_response)
            if json_match:
                try:
                    results = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

        if not results:
            # Fallback: wrap raw response
            logger.warning("Could not parse JSON, using raw response")
            results = {
                "exploration_id": EXPLORATION_ID,
                "query": QUERY,
                "summary": full_response[:500],
                "raw_response": full_response,
                "error": "Could not parse structured response",
                "confidence": "low"
            }
        else:
            # Ensure exploration_id is set
            results["exploration_id"] = EXPLORATION_ID
            results["query"] = QUERY

        # Save results
        output_path = Path("exploration_results.json")
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {output_path}")
        logger.info("Exploration completed successfully")

    except Exception as e:
        logger.error(f"Exploration failed: {e}", exc_info=True)

        # Save error results
        error_results = {
            "exploration_id": EXPLORATION_ID,
            "query": QUERY,
            "error": str(e),
            "status": "failed",
            "confidence": "none"
        }

        with open("exploration_results.json", "w") as f:
            json.dump(error_results, f, indent=2)

        raise


if __name__ == "__main__":
    asyncio.run(explore_codebase())
```

**Step 2: Test script locally (optional manual test)**

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export EXPLORATION_ID="test-001"
export QUERY="find all API endpoints"
export SCOPE="backend"
export FOCUS="files"

# Run script
cd .github/scripts
python explore_codebase.py

# Check output
cat ../../exploration_results.json
```

Expected: JSON file with exploration results

**Step 3: Commit script**

```bash
git add .github/scripts/explore_codebase.py
git commit -m "feat: add codebase exploration script with Claude SDK

- Initialize Claude SDK with system prompt
- Build context-aware prompts based on scope/focus
- Parse JSON results with fallback handling
- Save results to artifact file
- Comprehensive error handling and logging"
```

---

## Phase 3: Backend Tool Handler

### Task 4: Create Exploration Service

**Files:**
- Create: `backend/app/services/codebase_exploration_service.py`
- Create: `backend/tests/services/test_codebase_exploration_service.py`

**Step 1: Write test for exploration service**

Create: `backend/tests/services/test_codebase_exploration_service.py`

```python
"""Tests for CodebaseExplorationService."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.codebase_exploration_service import CodebaseExplorationService


@pytest.mark.asyncio
async def test_trigger_exploration(monkeypatch):
    """Test triggering a codebase exploration."""
    # Mock GitHubService
    mock_github_service = MagicMock()
    mock_github_service.trigger_workflow = AsyncMock(return_value={
        "id": 12345,
        "status": "queued",
        "html_url": "https://github.com/test/repo/actions/runs/12345"
    })

    service = CodebaseExplorationService(github_service=mock_github_service)

    result = await service.trigger_exploration(
        exploration_id="exp-001",
        query="how does authentication work",
        scope="backend",
        focus="architecture",
        callback_url="https://api.example.com/webhook"
    )

    assert result["exploration_id"] == "exp-001"
    assert result["status"] == "investigating"
    assert result["workflow_run_id"] == 12345

    # Verify workflow was triggered with correct inputs
    mock_github_service.trigger_workflow.assert_called_once()
    call_args = mock_github_service.trigger_workflow.call_args
    assert call_args[1]["workflow_name"] == "explore-codebase.yml"
    assert call_args[1]["inputs"]["query"] == "how does authentication work"
    assert call_args[1]["inputs"]["scope"] == "backend"


@pytest.mark.asyncio
async def test_generate_exploration_id():
    """Test exploration ID generation."""
    service = CodebaseExplorationService(github_service=MagicMock())

    exp_id_1 = service.generate_exploration_id("session-123")
    exp_id_2 = service.generate_exploration_id("session-123")

    # Should be unique
    assert exp_id_1 != exp_id_2

    # Should contain session prefix
    assert exp_id_1.startswith("session-123-exp-")


@pytest.mark.asyncio
async def test_format_results_for_agent():
    """Test formatting exploration results for agent context."""
    service = CodebaseExplorationService(github_service=MagicMock())

    results = {
        "exploration_id": "exp-001",
        "query": "find authentication",
        "summary": "Authentication uses JWT tokens",
        "relevant_files": [
            {"path": "auth.py", "purpose": "JWT handling", "importance": "high"}
        ],
        "code_examples": [
            {
                "file": "auth.py",
                "lines": "10-20",
                "snippet": "def verify_token()...",
                "explanation": "Token verification"
            }
        ],
        "confidence": "high"
    }

    formatted = service.format_results_for_agent(results)

    assert "Authentication uses JWT tokens" in formatted
    assert "auth.py" in formatted
    assert "JWT handling" in formatted
    assert "verify_token" in formatted
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/services/test_codebase_exploration_service.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement CodebaseExplorationService**

Create: `backend/app/services/codebase_exploration_service.py`

```python
"""Service for managing codebase exploration requests."""
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.services.github_service import GitHubService

logger = logging.getLogger(__name__)


class CodebaseExplorationService:
    """Service for triggering and managing codebase explorations."""

    def __init__(self, github_service: GitHubService):
        self.github_service = github_service

    def generate_exploration_id(self, session_id: str) -> str:
        """Generate unique exploration ID.

        Args:
            session_id: Session ID for context

        Returns:
            Unique exploration ID
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid4())[:8]
        return f"{session_id}-exp-{timestamp}-{unique_id}"

    async def trigger_exploration(
        self,
        exploration_id: str,
        query: str,
        scope: str = "full",
        focus: str = "patterns",
        callback_url: str | None = None,
    ) -> dict[str, Any]:
        """Trigger a codebase exploration workflow.

        Args:
            exploration_id: Unique ID for this exploration
            query: What to explore
            scope: Scope of exploration (backend/frontend/full)
            focus: What to focus on (files/patterns/architecture/dependencies)
            callback_url: Optional webhook URL for results

        Returns:
            Dictionary with exploration status and workflow info
        """
        logger.info(f"[EXPLORATION] Triggering exploration: {exploration_id}")
        logger.info(f"[EXPLORATION] Query: {query}")
        logger.info(f"[EXPLORATION] Scope: {scope}, Focus: {focus}")

        try:
            # Trigger GitHub workflow
            workflow_run = await self.github_service.trigger_workflow(
                workflow_name="explore-codebase.yml",
                inputs={
                    "exploration_id": exploration_id,
                    "query": query,
                    "scope": scope,
                    "focus": focus,
                    "callback_url": callback_url or "",
                }
            )

            logger.info(f"[EXPLORATION] Workflow triggered: run_id={workflow_run['id']}")

            return {
                "exploration_id": exploration_id,
                "status": "investigating",
                "workflow_run_id": workflow_run["id"],
                "workflow_url": workflow_run.get("html_url"),
                "query": query,
                "scope": scope,
                "focus": focus,
                "message": "🧐 Investigating codebase... This may take 1-2 minutes.",
            }

        except Exception as e:
            logger.error(f"[EXPLORATION] Failed to trigger workflow: {e}", exc_info=True)
            return {
                "exploration_id": exploration_id,
                "status": "failed",
                "error": str(e),
                "message": "Failed to start codebase exploration.",
            }

    async def get_exploration_results(
        self,
        exploration_id: str,
        workflow_run_id: int
    ) -> dict[str, Any] | None:
        """Get results from a completed exploration.

        Args:
            exploration_id: Exploration ID
            workflow_run_id: GitHub workflow run ID

        Returns:
            Exploration results dictionary or None if not ready
        """
        logger.info(f"[EXPLORATION] Fetching results for: {exploration_id}")

        try:
            # Check workflow status
            status = await self.github_service.check_workflow_status(workflow_run_id)

            if status["status"] != "completed":
                logger.info(f"[EXPLORATION] Workflow still {status['status']}")
                return None

            if status["conclusion"] != "success":
                logger.warning(f"[EXPLORATION] Workflow failed: {status['conclusion']}")
                return {
                    "exploration_id": exploration_id,
                    "status": "failed",
                    "error": f"Workflow concluded with: {status['conclusion']}",
                }

            # Download artifact
            artifact_name = f"exploration-{exploration_id}"
            results = await self.github_service.download_artifact_json(
                workflow_run_id,
                artifact_name
            )

            if not results:
                logger.error(f"[EXPLORATION] No results found in artifact")
                return {
                    "exploration_id": exploration_id,
                    "status": "failed",
                    "error": "No results found",
                }

            logger.info(f"[EXPLORATION] Results retrieved successfully")
            return results

        except Exception as e:
            logger.error(f"[EXPLORATION] Failed to get results: {e}", exc_info=True)
            return {
                "exploration_id": exploration_id,
                "status": "failed",
                "error": str(e),
            }

    def format_results_for_agent(self, results: dict[str, Any]) -> str:
        """Format exploration results as context for agent.

        Args:
            results: Exploration results dictionary

        Returns:
            Formatted string for injection into agent conversation
        """
        if results.get("error"):
            return f"⚠️ Exploration failed: {results['error']}"

        # Build formatted context
        parts = []

        # Summary
        if summary := results.get("summary"):
            parts.append(f"## Codebase Exploration Results\n\n{summary}")

        # Relevant files
        if files := results.get("relevant_files"):
            parts.append("\n### Relevant Files\n")
            for file in files[:5]:  # Limit to top 5
                path = file.get("path", "unknown")
                purpose = file.get("purpose", "")
                importance = file.get("importance", "")
                parts.append(f"- **{path}** ({importance}): {purpose}")

        # Key patterns
        if patterns := results.get("key_patterns"):
            parts.append("\n### Key Patterns Found\n")
            for pattern in patterns[:3]:  # Limit to top 3
                name = pattern.get("pattern", "")
                details = pattern.get("details", "")
                parts.append(f"- **{name}**: {details}")

        # Code examples
        if examples := results.get("code_examples"):
            parts.append("\n### Code Examples\n")
            for example in examples[:2]:  # Limit to 2 examples
                file = example.get("file", "")
                lines = example.get("lines", "")
                snippet = example.get("snippet", "")
                explanation = example.get("explanation", "")
                parts.append(f"\n**{file}** (lines {lines}):\n```\n{snippet}\n```\n{explanation}")

        # Architecture notes
        if arch := results.get("architecture_notes"):
            parts.append(f"\n### Architecture Notes\n\n{arch}")

        # Recommendations
        if recs := results.get("recommendations"):
            parts.append("\n### Recommendations\n")
            for rec in recs[:3]:
                parts.append(f"- {rec}")

        # Confidence
        if confidence := results.get("confidence"):
            parts.append(f"\n*Confidence: {confidence}*")

        return "\n".join(parts)
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest backend/tests/services/test_codebase_exploration_service.py -v
```

Expected: PASS - All tests pass

**Step 5: Commit**

```bash
git add backend/app/services/codebase_exploration_service.py backend/tests/services/test_codebase_exploration_service.py
git commit -m "feat: add CodebaseExplorationService

- Trigger exploration workflows with parameters
- Generate unique exploration IDs
- Fetch and parse exploration results
- Format results for agent context injection
- Add comprehensive service tests"
```

---

### Task 5: Integrate Tool Handler into WebSocket Flow

**Files:**
- Modify: `backend/app/api/brainstorms.py`
- Create: `backend/app/models/codebase_exploration.py`

**Step 1: Create model for tracking explorations**

Create: `backend/app/models/codebase_exploration.py`

```python
"""Models for codebase exploration tracking."""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.database import Base


class ExplorationStatus(str, enum.Enum):
    """Exploration status enum."""
    PENDING = "pending"
    INVESTIGATING = "investigating"
    COMPLETED = "completed"
    FAILED = "failed"


class CodebaseExploration(Base):
    """Track codebase exploration requests and results."""

    __tablename__ = "codebase_explorations"

    # Primary Key
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Context
    session_id: Mapped[str] = mapped_column(String(50), nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Request
    query: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default="full")
    focus: Mapped[str] = mapped_column(String(20), default="patterns")

    # GitHub Workflow
    workflow_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workflow_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Results
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    formatted_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[ExplorationStatus] = mapped_column(
        Enum(ExplorationStatus),
        default=ExplorationStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<CodebaseExploration(id='{self.id}', status='{self.status}')>"
```

**Step 2: Create migration**

```bash
cd backend
poetry run alembic revision -m "add codebase explorations table"
```

**Step 3: Write migration**

Edit the generated migration file:

```python
"""add codebase explorations table

Revision ID: XXXX
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade() -> None:
    op.create_table(
        'codebase_explorations',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('session_id', sa.String(50), nullable=False),
        sa.Column('message_id', sa.String(50), nullable=True),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('scope', sa.String(20), default='full'),
        sa.Column('focus', sa.String(20), default='patterns'),
        sa.Column('workflow_run_id', sa.Integer(), nullable=True),
        sa.Column('workflow_url', sa.String(500), nullable=True),
        sa.Column('results', JSONB, nullable=True),
        sa.Column('formatted_context', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_explorations_session', 'codebase_explorations', ['session_id'])
    op.create_index('idx_explorations_status', 'codebase_explorations', ['status'])


def downgrade() -> None:
    op.drop_table('codebase_explorations')
```

**Step 4: Run migration**

```bash
poetry run alembic upgrade head
```

Expected: Migration successful

**Step 5: Update models __init__.py**

Modify: `backend/app/models/__init__.py`

```python
from app.models.codebase_exploration import CodebaseExploration, ExplorationStatus

__all__ = [
    # ... existing exports
    "CodebaseExploration",
    "ExplorationStatus",
]
```

**Step 6: Commit**

```bash
git add backend/app/models/codebase_exploration.py backend/alembic/versions/ backend/app/models/__init__.py
git commit -m "feat: add codebase exploration tracking model

- Add CodebaseExploration model for tracking requests
- Store query, scope, focus parameters
- Track workflow run ID and results
- Add status enum (pending/investigating/completed/failed)
- Create database migration"
```

---

### Task 6: Handle Tool Calls in WebSocket

**Files:**
- Modify: `backend/app/api/brainstorms.py`

**Step 1: Write test for tool call handling**

Create: `backend/tests/api/test_brainstorms_tool_handling.py`

```python
"""Tests for tool handling in brainstorm WebSocket."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_handle_explore_codebase_tool_call(db_session):
    """Test handling explore_codebase tool call."""
    from app.api.brainstorms import handle_tool_call
    from app.models.codebase_exploration import CodebaseExploration, ExplorationStatus
    from sqlalchemy import select

    # Mock WebSocket
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()

    # Mock GitHub service
    mock_github = MagicMock()
    mock_github.trigger_workflow = AsyncMock(return_value={
        "id": 12345,
        "html_url": "https://github.com/test/actions/12345"
    })

    with patch('app.api.brainstorms.GitHubService', return_value=mock_github):
        result = await handle_tool_call(
            websocket=mock_ws,
            db=db_session,
            session_id="test-session",
            tool_name="explore_codebase",
            tool_input={
                "query": "find authentication code",
                "scope": "backend",
                "focus": "patterns"
            }
        )

    assert result is not None
    assert result["status"] == "investigating"

    # Verify exploration record created
    query = select(CodebaseExploration).where(
        CodebaseExploration.session_id == "test-session"
    )
    exp_result = await db_session.execute(query)
    exploration = exp_result.scalar_one_or_none()

    assert exploration is not None
    assert exploration.query == "find authentication code"
    assert exploration.scope == "backend"
    assert exploration.status == ExplorationStatus.INVESTIGATING

    # Verify WebSocket message sent
    mock_ws.send_json.assert_called_once()
    call_args = mock_ws.send_json.call_args[0][0]
    assert call_args["type"] == "tool_executing"
    assert "🧐" in call_args["message"]
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/api/test_brainstorms_tool_handling.py -v
```

Expected: FAIL - Function not implemented yet

**Step 3: Implement tool call handler in brainstorms.py**

Modify: `backend/app/api/brainstorms.py`

Add imports:

```python
from app.services.codebase_exploration_service import CodebaseExplorationService
from app.services.github_service import GitHubService
from app.models.codebase_exploration import CodebaseExploration, ExplorationStatus
```

Add handler function:

```python
async def handle_tool_call(
    websocket: WebSocket,
    db,
    session_id: str,
    tool_name: str,
    tool_input: dict[str, Any]
) -> dict[str, Any] | None:
    """Handle tool call from Claude.

    Args:
        websocket: WebSocket connection
        db: Database session
        session_id: Session ID
        tool_name: Name of tool being called
        tool_input: Tool input parameters

    Returns:
        Tool execution result or None
    """
    logger.info(f"[TOOL] Tool called: {tool_name}")
    logger.info(f"[TOOL] Input: {tool_input}")

    if tool_name == "explore_codebase":
        return await handle_explore_codebase(
            websocket, db, session_id, tool_input
        )

    logger.warning(f"[TOOL] Unknown tool: {tool_name}")
    return None


async def handle_explore_codebase(
    websocket: WebSocket,
    db,
    session_id: str,
    tool_input: dict[str, Any]
) -> dict[str, Any]:
    """Handle explore_codebase tool call.

    Args:
        websocket: WebSocket connection
        db: Database session
        session_id: Session ID
        tool_input: Tool parameters (query, scope, focus)

    Returns:
        Exploration status dictionary
    """
    query = tool_input.get("query", "")
    scope = tool_input.get("scope", "full")
    focus = tool_input.get("focus", "patterns")

    logger.info(f"[TOOL] Exploring codebase: query='{query}', scope={scope}, focus={focus}")

    # Initialize services
    github_service = GitHubService(
        token=settings.github_token,
        repo=settings.github_repo
    )
    exploration_service = CodebaseExplorationService(github_service)

    # Generate exploration ID
    exploration_id = exploration_service.generate_exploration_id(session_id)

    # Create exploration record
    exploration = CodebaseExploration(
        id=exploration_id,
        session_id=session_id,
        query=query,
        scope=scope,
        focus=focus,
        status=ExplorationStatus.PENDING,
    )
    db.add(exploration)
    await db.commit()
    await db.refresh(exploration)

    # Trigger exploration workflow
    callback_url = None
    if settings.webhook_base_url:
        callback_url = f"{settings.webhook_base_url}/api/v1/codebase-exploration/webhook/{exploration_id}"

    result = await exploration_service.trigger_exploration(
        exploration_id=exploration_id,
        query=query,
        scope=scope,
        focus=focus,
        callback_url=callback_url
    )

    # Update exploration with workflow info
    if result["status"] == "investigating":
        exploration.status = ExplorationStatus.INVESTIGATING
        exploration.workflow_run_id = result.get("workflow_run_id")
        exploration.workflow_url = result.get("workflow_url")
    else:
        exploration.status = ExplorationStatus.FAILED
        exploration.error_message = result.get("error")

    await db.commit()

    # Send status update to frontend
    await websocket.send_json({
        "type": "tool_executing",
        "tool_name": "explore_codebase",
        "exploration_id": exploration_id,
        "status": result["status"],
        "message": result["message"],
    })

    logger.info(f"[TOOL] Exploration triggered: {exploration_id}")

    return result
```

**Step 4: Integrate tool detection in stream_claude_response**

Modify `stream_claude_response` function in `backend/app/api/brainstorms.py`:

Add after the message streaming loop:

```python
async def stream_claude_response(
    websocket: WebSocket,
    db,
    session_id: str,
    agent_factory: AgentFactory
):
    """Stream Claude's response block-by-block."""
    # ... existing conversation history building ...

    message_id = str(uuid4())
    collected_blocks = []

    async with BrainstormingService(
        api_key=settings.anthropic_api_key,
        agent_factory=agent_factory,
        agent_name="brainstorm"
    ) as service:
        try:
            # Claude returns response with possible tool calls
            full_response = ""
            tool_calls = []  # Track tool calls

            async for chunk in service.stream_brainstorm_message(conversation):
                full_response += chunk

                # Check for tool use in chunks (SDK will emit tool_use messages)
                # For now, we parse from final response

            # Parse response for tool calls
            # NOTE: This is simplified - actual SDK emits ToolUseBlock messages
            # We'll detect them in the parsed blocks

            response_data = None
            try:
                json_text = extract_json_from_markdown(full_response)
                response_data = json.loads(json_text)
                blocks = response_data.get("blocks", [])

                for block in blocks:
                    if "id" not in block:
                        block["id"] = str(uuid4())

                    # Check if block indicates tool use
                    # Claude SDK actually sends ToolUseBlock objects
                    # For now, check if block has tool_use type
                    if block.get("type") == "tool_use":
                        tool_name = block.get("name")
                        tool_input = block.get("input", {})

                        logger.info(f"[WS] Tool use detected: {tool_name}")

                        # Handle tool call
                        tool_result = await handle_tool_call(
                            websocket, db, session_id,
                            tool_name, tool_input
                        )

                        tool_calls.append({
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_result": tool_result
                        })

                        # Don't send tool_use blocks to frontend
                        # Frontend will show tool execution status instead
                        continue

                    # Send regular blocks
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "message_id": message_id,
                        "block": block
                    })
                    collected_blocks.append(block)

            except json.JSONDecodeError as e:
                # ... existing fallback handling ...
                pass

            # Save message with tool calls metadata
            assistant_message = BrainstormMessage(
                id=message_id,
                session_id=session_id,
                role="assistant",
                content={
                    "blocks": collected_blocks,
                    "tool_calls": tool_calls,  # Store tool calls
                    "metadata": response_data.get("metadata", {}) if isinstance(response_data, dict) else {}
                }
            )
            db.add(assistant_message)
            await db.commit()

            # ... rest of existing code ...

        except Exception as e:
            # ... existing error handling ...
```

**Note**: The actual Claude Agent SDK emits `ToolUseBlock` objects that we need to detect. This is a simplified version. We'll need to update the `BrainstormingService` to properly handle and detect tool use blocks from the SDK.

**Step 5: Run tests**

```bash
poetry run pytest backend/tests/api/test_brainstorms_tool_handling.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/api/brainstorms.py backend/tests/api/test_brainstorms_tool_handling.py
git commit -m "feat: handle explore_codebase tool calls in WebSocket

- Add handle_tool_call dispatcher function
- Implement handle_explore_codebase handler
- Create CodebaseExploration record on tool call
- Trigger GitHub workflow via exploration service
- Send tool_executing status to frontend
- Add tool call tracking in message metadata
- Add comprehensive integration tests"
```

---

## Phase 4: Polling & Results Integration

### Task 7: Add Polling for Exploration Results

**Files:**
- Modify: `backend/app/services/polling_service.py`

**Step 1: Write test for exploration polling**

Create: `backend/tests/services/test_exploration_polling.py`

```python
"""Tests for exploration result polling."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.polling_service import PollingService
from app.models.codebase_exploration import CodebaseExploration, ExplorationStatus


@pytest.mark.asyncio
async def test_poll_exploring_explorations(db_session):
    """Test polling for explorations in INVESTIGATING status."""
    # Create test exploration
    exploration = CodebaseExploration(
        id="exp-001",
        session_id="session-123",
        query="test query",
        scope="full",
        focus="patterns",
        workflow_run_id=12345,
        status=ExplorationStatus.INVESTIGATING,
    )
    db_session.add(exploration)
    await db_session.commit()

    # Mock services
    mock_github = MagicMock()
    mock_github.check_workflow_status = AsyncMock(return_value={
        "status": "completed",
        "conclusion": "success"
    })
    mock_github.download_artifact_json = AsyncMock(return_value={
        "exploration_id": "exp-001",
        "summary": "Found authentication patterns",
        "confidence": "high"
    })

    with patch('app.services.polling_service.GitHubService', return_value=mock_github):
        polling_service = PollingService()
        await polling_service.poll_explorations()

    # Verify exploration updated
    await db_session.refresh(exploration)
    assert exploration.status == ExplorationStatus.COMPLETED
    assert exploration.results is not None
    assert exploration.formatted_context is not None
```

**Step 2: Modify polling_service.py**

Modify: `backend/app/services/polling_service.py`

Add exploration polling method:

```python
from app.models.codebase_exploration import CodebaseExploration, ExplorationStatus
from app.services.codebase_exploration_service import CodebaseExplorationService

class PollingService:
    # ... existing code ...

    async def poll_explorations(self):
        """Poll for completed codebase explorations."""
        async with async_session_maker() as db:
            try:
                # Find explorations in INVESTIGATING status
                result = await db.execute(
                    select(CodebaseExploration).where(
                        CodebaseExploration.status == ExplorationStatus.INVESTIGATING,
                        CodebaseExploration.workflow_run_id.isnot(None)
                    )
                )
                explorations = result.scalars().all()

                if not explorations:
                    return

                logger.info(f"[POLLING] Found {len(explorations)} explorations to check")

                # Initialize services
                github_service = GitHubService(
                    token=settings.github_token,
                    repo=settings.github_repo
                )
                exploration_service = CodebaseExplorationService(github_service)

                for exploration in explorations:
                    try:
                        logger.info(f"[POLLING] Checking exploration: {exploration.id}")

                        # Get results
                        results = await exploration_service.get_exploration_results(
                            exploration.id,
                            exploration.workflow_run_id
                        )

                        if not results:
                            # Still running
                            continue

                        # Update exploration with results
                        if results.get("status") == "failed":
                            exploration.status = ExplorationStatus.FAILED
                            exploration.error_message = results.get("error")
                        else:
                            exploration.status = ExplorationStatus.COMPLETED
                            exploration.results = results
                            exploration.formatted_context = exploration_service.format_results_for_agent(results)
                            exploration.completed_at = datetime.utcnow()

                        await db.commit()
                        logger.info(f"[POLLING] Updated exploration: {exploration.id} -> {exploration.status}")

                        # TODO: Notify WebSocket if still connected

                    except Exception as e:
                        logger.error(f"[POLLING] Error checking exploration {exploration.id}: {e}")
                        continue

            except Exception as e:
                logger.error(f"[POLLING] Error in poll_explorations: {e}")

    async def run(self):
        """Run polling loop."""
        logger.info("[POLLING] Starting polling service...")
        while True:
            try:
                await self.poll_analyzing_features()  # Existing
                await self.poll_explorations()  # New
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"[POLLING] Error in polling loop: {e}")
                await asyncio.sleep(self.interval)
```

**Step 3: Run tests**

```bash
poetry run pytest backend/tests/services/test_exploration_polling.py -v
```

Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/polling_service.py backend/tests/services/test_exploration_polling.py
git commit -m "feat: add polling for exploration results

- Poll explorations in INVESTIGATING status
- Fetch results from GitHub artifacts
- Update exploration status and results
- Format context for agent injection
- Integrate into existing polling service loop"
```

---

## Phase 5: Frontend Integration

### Task 8: Add Tool Execution UI State

**Files:**
- Modify: `frontend/src/stores/brainstorm.ts`
- Modify: `frontend/src/types/brainstorm.ts`

**Step 1: Add types for tool execution**

Modify: `frontend/src/types/brainstorm.ts`

```typescript
// Add to existing types

export interface ToolExecution {
  tool_name: string
  exploration_id: string
  status: 'investigating' | 'completed' | 'failed'
  message: string
  started_at: string
}

// Update WSServerMessage union
export type WSServerMessage =
  | WSUserMessageSaved
  | WSStreamChunk
  | WSStreamComplete
  | WSToolExecuting  // New
  | WSError

export interface WSToolExecuting {
  type: 'tool_executing'
  tool_name: string
  exploration_id: string
  status: string
  message: string
}
```

**Step 2: Add tool execution state to store**

Modify: `frontend/src/stores/brainstorm.ts`

```typescript
export const useBrainstormStore = defineStore('brainstorm', () => {
  // ... existing state ...

  const activeToolExecution = ref<ToolExecution | null>(null)

  // ... existing functions ...

  function setToolExecuting(execution: ToolExecution) {
    activeToolExecution.value = execution
  }

  function clearToolExecution() {
    activeToolExecution.value = null
  }

  return {
    // ... existing exports ...
    activeToolExecution,
    setToolExecuting,
    clearToolExecution,
  }
})
```

**Step 3: Commit**

```bash
git add frontend/src/stores/brainstorm.ts frontend/src/types/brainstorm.ts
git commit -m "feat: add tool execution state to brainstorm store

- Add ToolExecution interface
- Add WSToolExecuting message type
- Add activeToolExecution state
- Add setToolExecuting and clearToolExecution actions"
```

---

### Task 9: Display Tool Execution Status

**Files:**
- Create: `frontend/src/components/brainstorm/ToolExecutionStatus.vue`
- Modify: `frontend/src/components/BrainstormChat.vue`

**Step 1: Create ToolExecutionStatus component**

Create: `frontend/src/components/brainstorm/ToolExecutionStatus.vue`

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { ToolExecution } from '@/types/brainstorm'

const props = defineProps<{
  execution: ToolExecution
}>()

const statusEmoji = computed(() => {
  switch (props.execution.status) {
    case 'investigating':
      return '🧐'
    case 'completed':
      return '✅'
    case 'failed':
      return '❌'
    default:
      return '⏳'
  }
})

const statusColor = computed(() => {
  switch (props.execution.status) {
    case 'investigating':
      return 'text-blue-600'
    case 'completed':
      return 'text-green-600'
    case 'failed':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
})
</script>

<template>
  <div class="bg-accent/20 rounded-lg p-4 border border-accent">
    <div class="flex items-start gap-3">
      <span class="text-2xl flex-shrink-0">{{ statusEmoji }}</span>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-sm font-semibold" :class="statusColor">
            {{ execution.status === 'investigating' ? 'Investigating Codebase' : execution.status }}
          </span>
        </div>
        <p class="text-sm text-muted-foreground">
          {{ execution.message }}
        </p>
        <div v-if="execution.status === 'investigating'" class="flex gap-1 mt-2">
          <div class="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:-0.3s]"></div>
          <div class="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:-0.15s]"></div>
          <div class="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce"></div>
        </div>
      </div>
    </div>
  </div>
</template>
```

**Step 2: Integrate into BrainstormChat**

Modify: `frontend/src/components/BrainstormChat.vue`

Add import:

```typescript
import ToolExecutionStatus from '@/components/brainstorm/ToolExecutionStatus.vue'
```

Add to template after messages and before input:

```vue
<!-- Tool Execution Status -->
<div v-if="store.activeToolExecution" class="px-4 pb-4">
  <ToolExecutionStatus :execution="store.activeToolExecution" />
</div>
```

Update WebSocket message handler:

```typescript
function handleServerMessage(data: WSServerMessage) {
  switch (data.type) {
    // ... existing cases ...

    case 'tool_executing':
      console.log('[WS] Tool executing:', (data as any).tool_name)
      store.setToolExecuting({
        tool_name: (data as any).tool_name,
        exploration_id: (data as any).exploration_id,
        status: (data as any).status,
        message: (data as any).message,
        started_at: new Date().toISOString(),
      })
      scrollToBottom()
      break

    case 'stream_chunk':
      // Clear tool execution when response starts
      if (store.activeToolExecution) {
        store.clearToolExecution()
      }
      // ... existing code ...
      break

    // ... other cases ...
  }
}
```

**Step 3: Test in browser**

```bash
npm run dev
# Create brainstorm session and trigger exploration
# (Will need backend implementation complete first)
```

Expected: See "🧐 Investigating Codebase..." status appear

**Step 4: Commit**

```bash
git add frontend/src/components/brainstorm/ToolExecutionStatus.vue frontend/src/components/BrainstormChat.vue
git commit -m "feat: display tool execution status in chat

- Create ToolExecutionStatus component
- Show investigating indicator with animated dots
- Display status emoji and message
- Handle tool_executing WebSocket message
- Clear status when response arrives"
```

---

## Phase 6: Testing & Documentation

### Task 10: End-to-End Integration Test

**Files:**
- Create: `backend/tests/integration/test_codebase_exploration_flow.py`

**Step 1: Write integration test**

Create: `backend/tests/integration/test_codebase_exploration_flow.py`

```python
"""End-to-end integration test for codebase exploration."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_exploration_flow(db_session):
    """Test complete exploration flow from tool call to results."""
    from app.services.codebase_exploration_service import CodebaseExplorationService
    from app.models.codebase_exploration import CodebaseExploration, ExplorationStatus
    from sqlalchemy import select

    # Mock GitHub service
    mock_github = MagicMock()
    mock_github.trigger_workflow = AsyncMock(return_value={
        "id": 99999,
        "html_url": "https://github.com/test/actions/99999"
    })
    mock_github.check_workflow_status = AsyncMock(return_value={
        "status": "completed",
        "conclusion": "success"
    })
    mock_github.download_artifact_json = AsyncMock(return_value={
        "exploration_id": "test-exp-001",
        "query": "find auth",
        "summary": "Authentication uses JWT tokens stored in HTTP-only cookies",
        "relevant_files": [
            {
                "path": "backend/app/auth/jwt.py",
                "purpose": "JWT token generation and validation",
                "importance": "high"
            }
        ],
        "key_patterns": [
            {
                "pattern": "JWT Authentication",
                "details": "Tokens generated on login, validated on each request",
                "examples": ["create_access_token()", "verify_token()"]
            }
        ],
        "confidence": "high"
    })

    # Step 1: Trigger exploration
    service = CodebaseExplorationService(mock_github)

    exploration_id = "test-exp-001"
    result = await service.trigger_exploration(
        exploration_id=exploration_id,
        query="find auth",
        scope="backend",
        focus="patterns"
    )

    assert result["status"] == "investigating"
    assert result["workflow_run_id"] == 99999

    # Step 2: Simulate polling - get results
    results = await service.get_exploration_results(
        exploration_id=exploration_id,
        workflow_run_id=99999
    )

    assert results is not None
    assert results["summary"] == "Authentication uses JWT tokens stored in HTTP-only cookies"
    assert len(results["relevant_files"]) == 1

    # Step 3: Format for agent
    formatted = service.format_results_for_agent(results)

    assert "JWT tokens" in formatted
    assert "jwt.py" in formatted
    assert "high" in formatted

    print("\n" + "="*60)
    print("Formatted Context for Agent:")
    print("="*60)
    print(formatted)
    print("="*60)
```

**Step 2: Run integration test**

```bash
poetry run pytest backend/tests/integration/test_codebase_exploration_flow.py -v -s
```

Expected: PASS with formatted output displayed

**Step 3: Commit**

```bash
git add backend/tests/integration/test_codebase_exploration_flow.py
git commit -m "test: add end-to-end integration test for exploration

- Test complete flow from trigger to results
- Mock GitHub workflow execution
- Verify result formatting
- Display formatted context output"
```

---

### Task 11: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Create: `docs/guides/codebase-exploration.md`

**Step 1: Update CLAUDE.md**

Modify: `CLAUDE.md`

Add section after Dynamic Tools System:

```markdown
## Codebase Exploration

Agents can explore the codebase to gather technical context using the `explore_codebase` tool.

### How It Works

1. **Agent needs context**: During conversation, agent realizes it needs to understand existing implementation
2. **Tool invocation**: Agent calls `explore_codebase(query="how authentication works", scope="backend")`
3. **GitHub workflow**: Backend triggers GitHub Actions workflow with Claude Agent SDK
4. **Exploration**: Claude explores repo using Read, Glob, Grep, Bash tools
5. **Results returned**: Findings returned as artifact and injected back into conversation
6. **Agent continues**: Agent uses context to provide informed response

### Frontend UX

While exploration runs (1-2 minutes), frontend displays:
```
🧐 Investigating Codebase...
Claude is exploring the repository to gather context...
```

### Available Parameters

- **query**: What to investigate (e.g., "how authentication works", "find API endpoints")
- **scope**: Which part to explore
  - `backend`: Python/FastAPI code only
  - `frontend`: Vue/TypeScript code only
  - `full`: Entire repository
- **focus**: What aspect to focus on
  - `patterns`: Code patterns and implementations (default)
  - `files`: File structure and organization
  - `architecture`: How components relate
  - `dependencies`: Imports and relationships

### Example Explorations

```
Query: "how does authentication work"
Scope: backend
Focus: architecture
→ Returns: JWT implementation, middleware flow, security measures

Query: "list all API endpoints"
Scope: backend
Focus: files
→ Returns: All route definitions with methods and purposes

Query: "find the user model"
Scope: backend
Focus: patterns
→ Returns: SQLAlchemy model definition, relationships, methods
```

### Limitations

- Maximum 5 minutes exploration time
- Results limited to most relevant findings
- Cannot modify code, only read
- One exploration at a time per session

See `docs/guides/codebase-exploration.md` for technical details.
```

**Step 2: Create detailed guide**

Create: `docs/guides/codebase-exploration.md`

```markdown
# Codebase Exploration - Technical Guide

## Overview

The Codebase Exploration system allows Claude agents to explore the repository using GitHub Actions, providing technical context without direct backend access to the codebase.

## Architecture

```
Agent → explore_codebase tool → Backend → GitHub Workflow → Claude SDK
                                              ↓
                                         Explore repo
                                              ↓
                                    Generate findings JSON
                                              ↓
Backend polls/webhook ← Artifact ← Workflow completes
        ↓
Format context → Inject into conversation → Agent continues
```

## Components

### 1. Tool Definition (`explore_codebase`)

Registered in `tools` table with schema:

```json
{
  "input_schema": {
    "properties": {
      "query": {"type": "string"},
      "scope": {"enum": ["backend", "frontend", "full"]},
      "focus": {"enum": ["patterns", "files", "architecture", "dependencies"]}
    }
  }
}
```

### 2. GitHub Workflow (`.github/workflows/explore-codebase.yml`)

- Triggered via workflow_dispatch
- Runs Python script with Claude Agent SDK
- Claude has access to: Glob, Grep, Read, Bash
- Generates JSON results
- Uploads as artifact (1 day retention)

### 3. Exploration Script (`.github/scripts/explore_codebase.py`)

- Initializes Claude with specialized system prompt
- Builds context-aware query based on scope/focus
- Parses structured JSON results
- Handles errors gracefully

### 4. Backend Service (`CodebaseExplorationService`)

**Methods:**
- `trigger_exploration()`: Start workflow with parameters
- `get_exploration_results()`: Poll for completion and download artifact
- `format_results_for_agent()`: Convert to readable context

### 5. Database Tracking (`CodebaseExploration` model)

Tracks each exploration:
- exploration_id (unique)
- session_id (which brainstorm session)
- query, scope, focus (parameters)
- workflow_run_id (GitHub workflow)
- results (JSON artifact)
- status (pending → investigating → completed/failed)

### 6. Frontend UI

**Components:**
- `ToolExecutionStatus.vue`: Shows "🧐 Investigating..." status
- Updates via WebSocket when tool executed
- Clears when response arrives

## Usage from Agent Perspective

When agent code runs in backend:

```python
# Agent realizes it needs context
response = "I need to understand how authentication is implemented"

# SDK detects need and calls tool
tool_use = {
    "name": "explore_codebase",
    "input": {
        "query": "how authentication works",
        "scope": "backend",
        "focus": "architecture"
    }
}

# Backend handles tool call
exploration = trigger_exploration(...)

# Workflow runs (1-2 minutes)
# Results appear in exploration.results

# Backend formats and re-injects
context = format_results_for_agent(exploration.results)

# Agent continues with context
response = f"Based on the codebase exploration:\n{context}\n\nTo implement your feature..."
```

## Results Format

Exploration returns structured JSON:

```json
{
  "exploration_id": "session-123-exp-20260109120000-abc123",
  "query": "how authentication works",
  "summary": "2-3 sentence overview",
  "relevant_files": [
    {
      "path": "backend/app/auth/jwt.py",
      "purpose": "JWT token management",
      "importance": "high"
    }
  ],
  "key_patterns": [
    {
      "pattern": "JWT Authentication",
      "details": "Tokens generated on login...",
      "examples": ["create_access_token()", "verify_token()"]
    }
  ],
  "code_examples": [
    {
      "file": "backend/app/auth/jwt.py",
      "lines": "25-40",
      "snippet": "def create_access_token(data: dict):\n    ...",
      "explanation": "Creates JWT with expiration"
    }
  ],
  "architecture_notes": "Auth middleware validates tokens on each request...",
  "recommendations": ["Consider adding refresh tokens", "..."],
  "confidence": "high"
}
```

## Polling vs Webhook

**Localhost (development):**
- Uses polling every 30 seconds
- Checks explorations in `INVESTIGATING` status
- Downloads artifacts when complete

**Production (with webhook URL):**
- Workflow sends webhook on completion
- Immediate notification
- Polling as backup

## Security Considerations

1. **Read-only**: Exploration can only read code, never modify
2. **Timeout**: 5 minute maximum runtime
3. **Rate limiting**: Usage_limit=10 per session
4. **Secrets**: ANTHROPIC_API_KEY required in GitHub secrets
5. **Audit trail**: All explorations logged in database

## Troubleshooting

### Exploration Stuck in "investigating"

1. Check workflow status on GitHub Actions
2. Look for workflow failures or timeouts
3. Check artifact was uploaded
4. Verify polling service is running

### Empty Results

1. Scope may be too narrow (try "full")
2. Query may be too vague (be specific)
3. Check exploration logs in workflow

### Exploration Failed

1. Check `error_message` in exploration record
2. Common issues:
   - API key invalid
   - Timeout (complex query)
   - Parse error (Claude didn't return JSON)

## Performance

- **Trigger time**: <1 second
- **Exploration time**: 30 seconds - 3 minutes
- **Typical time**: 1-2 minutes
- **Polling interval**: 30 seconds

## Future Enhancements

1. **Real-time streaming**: Stream exploration progress to frontend
2. **Caching**: Cache common queries for instant results
3. **Multiple agents**: Allow multiple explorations in parallel
4. **Incremental results**: Show findings as they're discovered
5. **Tool chaining**: Automatically trigger follow-up explorations
```

**Step 3: Commit**

```bash
git add CLAUDE.md docs/guides/codebase-exploration.md
git commit -m "docs: document codebase exploration system

- Add overview to CLAUDE.md
- Create comprehensive technical guide
- Document architecture and components
- Include usage examples and troubleshooting
- Document security considerations"
```

---

## Execution Complete

**Summary:**

You have successfully implemented a complete Codebase Exploration Tool with:

✅ **Tool Definition**: explore_codebase registered in database
✅ **GitHub Workflow**: Automated exploration with Claude Agent SDK
✅ **Exploration Script**: Intelligent codebase investigation
✅ **Backend Services**: CodebaseExplorationService + tool handler
✅ **Database Tracking**: Full exploration lifecycle tracking
✅ **Polling Integration**: Results retrieval via existing infrastructure
✅ **Frontend UI**: "🧐 Investigating..." status display
✅ **Testing**: Unit + integration tests
✅ **Documentation**: Comprehensive guides

**Agent Capabilities:**

Agents can now:
- Request codebase exploration during conversation
- Specify query, scope, and focus
- Wait for results (1-2 minutes)
- Receive formatted context
- Provide informed responses with technical details

**User Experience:**

Users see:
1. Agent realizes it needs context
2. "🧐 Investigating Codebase..." appears
3. (1-2 minute wait with animated indicator)
4. Agent responds with informed answer

---

**Plan complete and saved to `docs/plans/2026-01-09-codebase-exploration-tool.md`.**

Two execution options:

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)**
- Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
