#!/usr/bin/env python3
"""Update brainstorm agent system prompt to document explore_codebase tool."""
import sys
import asyncio
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select  # noqa: E402
from app.database import async_session_maker  # noqa: E402
from app.models.agent import AgentType  # noqa: E402


TOOLS_SECTION = '''

## Available Tools

You have access to a special tool to help with your work:

### explore_codebase
Use this tool when the PM wants to understand technical aspects of the existing codebase. This triggers an automated exploration of the repository.

**When to use:**
- PM asks about existing implementations ("how is X implemented?")
- PM wants to understand technical constraints
- PM needs to know what's already built
- Assessing feasibility of new features
- Understanding architecture or patterns

**Parameters:**
- query: What you want to explore (required) - e.g., "How is authentication implemented?"
- scope: "full", "backend", or "frontend" (default: "full")
- focus: "patterns", "files", "architecture", or "dependencies" (default: "patterns")

**Example usage:**
When PM says "I want to add social login, what do we have for auth currently?", use the tool with:
- query: "authentication and login implementation"
- scope: "backend"
- focus: "architecture"

The tool will explore the codebase and return structured findings that you can use to inform your response. While waiting for results, let the PM know you're investigating the codebase.

**Important:** Only use this tool when the PM specifically asks about technical implementation or existing code. For pure feature discovery without technical context, just proceed with the brainstorming conversation.
'''


async def update_system_prompt():
    """Update the brainstorm agent system prompt."""
    print("\n" + "=" * 60)
    print("Updating Brainstorm Agent System Prompt")
    print("=" * 60 + "\n")

    async with async_session_maker() as db:
        result = await db.execute(
            select(AgentType).where(AgentType.name == "brainstorm")
        )
        agent = result.scalar_one_or_none()

        if not agent:
            print("Brainstorm agent not found")
            return False

        if not agent.system_prompt:
            print("Agent has no system prompt - cannot update")
            return False

        # Check if already contains explore_codebase
        if "explore_codebase" in agent.system_prompt:
            print("System prompt already mentions explore_codebase")
            return True

        # Append tools section
        agent.system_prompt = agent.system_prompt + TOOLS_SECTION
        await db.commit()

        print("Updated brainstorm agent system prompt with explore_codebase tool")
        print(f"\nAdded {len(TOOLS_SECTION)} characters to system prompt")
        return True


if __name__ == "__main__":
    success = asyncio.run(update_system_prompt())
    sys.exit(0 if success else 1)
