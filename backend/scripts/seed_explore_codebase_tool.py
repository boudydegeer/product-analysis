#!/usr/bin/env python3
"""Seed script for explore_codebase tool."""
import sys
import asyncio
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import after path modification - this is intentional
from sqlalchemy import select  # noqa: E402
from app.database import async_session_maker  # noqa: E402
from app.models.agent import AgentType, AgentToolConfig  # noqa: E402
from app.models.tool import Tool  # noqa: E402


EXPLORE_CODEBASE_TOOL = {
    "name": "explore_codebase",
    "description": (
        "Explore the codebase to gather technical context. Uses Claude Agent SDK "
        "via GitHub Actions to analyze code patterns, architecture, and dependencies."
    ),
    "category": "codebase",
    "tool_type": "async_workflow",
    "definition": {
        "name": "explore_codebase",
        "description": (
            "Explore the codebase to understand technical context, find relevant files, "
            "identify patterns, and analyze architecture."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "What you want to learn about the codebase "
                        "(e.g., 'How is authentication implemented?', "
                        "'Find all API endpoints', 'Explain the database schema')"
                    ),
                },
                "scope": {
                    "type": "string",
                    "enum": ["full", "backend", "frontend"],
                    "description": "Which part of codebase to explore. Default: full",
                    "default": "full",
                },
                "focus": {
                    "type": "string",
                    "enum": ["patterns", "files", "architecture", "dependencies"],
                    "description": "What aspect to focus on. Default: patterns",
                    "default": "patterns",
                },
            },
            "required": ["query"],
        },
    },
    "enabled": True,
    "is_dangerous": False,
    "requires_approval": False,
    "version": "1.0.0",
    "tags": ["codebase", "exploration", "github-actions"],
    "created_by": "system",
}


async def seed_explore_codebase_tool(db):
    """Create the explore_codebase tool if it doesn't exist."""
    print("🔧 Seeding explore_codebase tool...")

    # Check if tool already exists
    result = await db.execute(
        select(Tool).where(Tool.name == EXPLORE_CODEBASE_TOOL["name"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  ⏭️  Tool '{EXPLORE_CODEBASE_TOOL['name']}' already exists")
        return existing

    tool = Tool(**EXPLORE_CODEBASE_TOOL)
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    print(f"  ✅ Created tool: {EXPLORE_CODEBASE_TOOL['name']}")
    return tool


async def assign_tool_to_brainstorm_agent(db):
    """Assign explore_codebase tool to brainstorm agent with usage_limit=10."""
    print("🔗 Assigning explore_codebase to brainstorm agent...")

    # Get the brainstorm agent
    result = await db.execute(select(AgentType).where(AgentType.name == "brainstorm"))
    brainstorm_agent = result.scalar_one_or_none()

    if not brainstorm_agent:
        print("  ⚠️  Brainstorm agent not found, skipping tool assignment")
        return

    # Get the explore_codebase tool
    result = await db.execute(select(Tool).where(Tool.name == "explore_codebase"))
    tool = result.scalar_one_or_none()

    if not tool:
        print("  ⚠️  explore_codebase tool not found, skipping assignment")
        return

    # Check if assignment already exists
    result = await db.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == brainstorm_agent.id,
            AgentToolConfig.tool_id == tool.id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  ⏭️  Tool '{tool.name}' already assigned to brainstorm agent")
        return

    # Create assignment with tool_order=3 and usage_limit=10
    config = AgentToolConfig(
        agent_type_id=brainstorm_agent.id,
        tool_id=tool.id,
        enabled_for_agent=True,
        order_index=3,  # After create_plan=1 and web_search=2
        allow_use=True,
        requires_approval=False,
        usage_limit=10,
    )
    db.add(config)
    await db.commit()
    print(f"  ✅ Assigned tool: {tool.name} → brainstorm agent (usage_limit=10)")


async def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("🌱 SEEDING EXPLORE_CODEBASE TOOL")
    print("=" * 60 + "\n")

    async with async_session_maker() as db:
        try:
            await seed_explore_codebase_tool(db)
            await assign_tool_to_brainstorm_agent(db)

            print("\n" + "=" * 60)
            print("✅ SEEDING COMPLETED SUCCESSFULLY")
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
