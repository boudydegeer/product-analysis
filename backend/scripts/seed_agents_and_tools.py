#!/usr/bin/env python3
"""Seed script for default agents and tools."""
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
from app.services.brainstorming_service import BrainstormingService  # noqa: E402


async def seed_default_tools(db):
    """Create default tools if they don't exist."""
    print("🔧 Seeding default tools...")

    tools_data = [
        {
            "name": "create_plan",
            "description": "Creates a structured implementation plan document",
            "category": "planning",
            "tool_type": "builtin",
            "definition": {
                "type": "function",
                "function": {
                    "name": "create_plan",
                    "description": "Creates a structured implementation plan document with tasks, dependencies, and success criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "tasks": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "dependencies": {"type": "array", "items": {"type": "string"}}
                                    }
                                }
                            }
                        },
                        "required": ["title", "description", "tasks"]
                    }
                }
            },
            "enabled": True,
            "is_dangerous": False,
            "requires_approval": False,
            "version": "1.0.0",
            "tags": ["planning", "documentation"],
            "example_usage": "Use this tool to create a detailed implementation plan after brainstorming a feature.",
            "created_by": "system"
        },
        {
            "name": "web_search",
            "description": "Searches the web for information",
            "category": "research",
            "tool_type": "builtin",
            "definition": {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Performs a web search and returns relevant results",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            "enabled": True,
            "is_dangerous": False,
            "requires_approval": False,
            "version": "1.0.0",
            "tags": ["research", "web", "information"],
            "example_usage": "Use this tool to research best practices, competitive features, or technical approaches.",
            "created_by": "system"
        }
    ]

    created_count = 0
    for tool_data in tools_data:
        # Check if tool already exists
        result = await db.execute(
            select(Tool).where(Tool.name == tool_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  ⏭️  Tool '{tool_data['name']}' already exists")
        else:
            tool = Tool(**tool_data)
            db.add(tool)
            print(f"  ✅ Created tool: {tool_data['name']}")
            created_count += 1

    await db.commit()
    print(f"🔧 Tools seeded: {created_count} created, {len(tools_data) - created_count} existing\n")


async def seed_default_agent_types(db):
    """Create default agent types if they don't exist."""
    print("🤖 Seeding default agent types...")

    agent_types_data = [
        {
            "name": "brainstorm",
            "display_name": "Brainstorm Assistant",
            "description": "AI Product Discovery facilitator for defining actionable features",
            "avatar_url": None,
            "avatar_color": "#6366f1",
            "personality_traits": [
                "strategic",
                "concise",
                "action-oriented",
                "business-focused",
                "non-technical"
            ],
            "model": "claude-sonnet-4-5",
            "system_prompt": BrainstormingService.SYSTEM_PROMPT,
            "streaming_enabled": True,
            "max_context_tokens": 200000,
            "temperature": 0.7,
            "enabled": True,
            "is_default": True,
            "version": "1.0.0"
        }
    ]

    created_count = 0
    for agent_data in agent_types_data:
        # Check if agent type already exists
        result = await db.execute(
            select(AgentType).where(AgentType.name == agent_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  ⏭️  Agent type '{agent_data['name']}' already exists")
        else:
            agent_type = AgentType(**agent_data)
            db.add(agent_type)
            print(f"  ✅ Created agent type: {agent_data['display_name']}")
            created_count += 1

    await db.commit()
    print(f"🤖 Agent types seeded: {created_count} created, {len(agent_types_data) - created_count} existing\n")


async def assign_tools_to_agents(db):
    """Assign tools to agent types."""
    print("🔗 Assigning tools to agents...")

    # Get the brainstorm agent
    result = await db.execute(
        select(AgentType).where(AgentType.name == "brainstorm")
    )
    brainstorm_agent = result.scalar_one_or_none()

    if not brainstorm_agent:
        print("  ⚠️  Brainstorm agent not found, skipping tool assignment")
        return

    # Get the tools
    tool_names = ["create_plan", "web_search"]
    result = await db.execute(
        select(Tool).where(Tool.name.in_(tool_names))
    )
    tools = result.scalars().all()

    if not tools:
        print("  ⚠️  No tools found, skipping assignment")
        return

    assigned_count = 0
    for i, tool in enumerate(tools):
        # Check if assignment already exists
        result = await db.execute(
            select(AgentToolConfig).where(
                AgentToolConfig.agent_type_id == brainstorm_agent.id,
                AgentToolConfig.tool_id == tool.id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  ⏭️  Tool '{tool.name}' already assigned to brainstorm agent")
        else:
            config = AgentToolConfig(
                agent_type_id=brainstorm_agent.id,
                tool_id=tool.id,
                enabled_for_agent=True,
                order_index=i,
                allow_use=True,
                requires_approval=False,
                usage_limit=None
            )
            db.add(config)
            print(f"  ✅ Assigned tool: {tool.name} → brainstorm agent")
            assigned_count += 1

    await db.commit()
    print(f"🔗 Tool assignments completed: {assigned_count} created, {len(tools) - assigned_count} existing\n")


async def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("🌱 SEEDING DEFAULT AGENTS AND TOOLS")
    print("=" * 60 + "\n")

    async with async_session_maker() as db:
        try:
            await seed_default_tools(db)
            await seed_default_agent_types(db)
            await assign_tools_to_agents(db)

            print("=" * 60)
            print("✅ SEEDING COMPLETED SUCCESSFULLY")
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
