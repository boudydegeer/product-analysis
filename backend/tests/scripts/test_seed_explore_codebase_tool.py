"""Tests for seed_explore_codebase_tool script."""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig


class TestSeedExploreCodebaseTool:
    """Test cases for the explore_codebase tool seeding."""

    @pytest.fixture
    async def brainstorm_agent(self, db_session: AsyncSession) -> AgentType:
        """Create a brainstorm agent for testing."""
        agent = AgentType(
            name="brainstorm",
            display_name="Brainstorm Assistant",
            description="AI Product Discovery facilitator",
            model="claude-sonnet-4-5",
            system_prompt="Test system prompt",
            enabled=True,
            is_default=True,
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)
        return agent

    @pytest.fixture
    async def existing_tools(self, db_session: AsyncSession) -> list[Tool]:
        """Create existing tools (create_plan and web_search) for testing."""
        tools = [
            Tool(
                name="create_plan",
                description="Creates a structured implementation plan",
                category="planning",
                tool_type="builtin",
                definition={"type": "function"},
                enabled=True,
                version="1.0.0",
                tags=["planning"],
                created_by="system",
            ),
            Tool(
                name="web_search",
                description="Searches the web for information",
                category="research",
                tool_type="builtin",
                definition={"type": "function"},
                enabled=True,
                version="1.0.0",
                tags=["research"],
                created_by="system",
            ),
        ]
        for tool in tools:
            db_session.add(tool)
        await db_session.commit()
        return tools

    async def test_tool_created_with_correct_properties(
        self, db_session: AsyncSession, brainstorm_agent: AgentType
    ):
        """Test that explore_codebase tool is created with correct properties."""
        # Import the seeding functions
        from scripts.seed_explore_codebase_tool import seed_explore_codebase_tool

        # Run the seeding function
        await seed_explore_codebase_tool(db_session)

        # Verify tool was created
        result = await db_session.execute(
            select(Tool).where(Tool.name == "explore_codebase")
        )
        tool = result.scalar_one_or_none()

        assert tool is not None
        assert tool.name == "explore_codebase"
        assert "Explore the codebase to gather technical context" in tool.description
        assert tool.category == "codebase"
        assert tool.tool_type == "async_workflow"
        assert tool.enabled is True
        assert tool.is_dangerous is False
        assert tool.requires_approval is False
        assert tool.version == "1.0.0"
        assert tool.created_by == "system"

        # Verify tags
        assert "codebase" in tool.tags
        assert "exploration" in tool.tags
        assert "github-actions" in tool.tags

        # Verify definition structure
        assert tool.definition is not None
        assert tool.definition["name"] == "explore_codebase"
        assert "input_schema" in tool.definition
        assert "properties" in tool.definition["input_schema"]
        assert "query" in tool.definition["input_schema"]["properties"]
        assert "scope" in tool.definition["input_schema"]["properties"]
        assert "focus" in tool.definition["input_schema"]["properties"]
        assert tool.definition["input_schema"]["required"] == ["query"]

        # Verify scope enum values
        scope_def = tool.definition["input_schema"]["properties"]["scope"]
        assert scope_def["enum"] == ["full", "backend", "frontend"]
        assert scope_def["default"] == "full"

        # Verify focus enum values
        focus_def = tool.definition["input_schema"]["properties"]["focus"]
        assert focus_def["enum"] == [
            "patterns",
            "files",
            "architecture",
            "dependencies",
        ]
        assert focus_def["default"] == "patterns"

    async def test_script_is_idempotent(
        self, db_session: AsyncSession, brainstorm_agent: AgentType
    ):
        """Test that running the script twice doesn't create duplicates."""
        from scripts.seed_explore_codebase_tool import seed_explore_codebase_tool

        # Run the seeding function twice
        await seed_explore_codebase_tool(db_session)
        await seed_explore_codebase_tool(db_session)

        # Verify only one tool was created
        result = await db_session.execute(
            select(Tool).where(Tool.name == "explore_codebase")
        )
        tools = result.scalars().all()

        assert len(tools) == 1

    async def test_tool_assigned_to_brainstorm_agent_with_usage_limit(
        self,
        db_session: AsyncSession,
        brainstorm_agent: AgentType,
        existing_tools: list[Tool],
    ):
        """Test that tool is assigned to brainstorm agent with usage_limit=10."""
        from scripts.seed_explore_codebase_tool import (
            seed_explore_codebase_tool,
            assign_tool_to_brainstorm_agent,
        )

        # First create the tool
        await seed_explore_codebase_tool(db_session)

        # Get the created tool
        result = await db_session.execute(
            select(Tool).where(Tool.name == "explore_codebase")
        )
        tool = result.scalar_one()

        # Assign to agent
        await assign_tool_to_brainstorm_agent(db_session)

        # Verify assignment
        result = await db_session.execute(
            select(AgentToolConfig).where(
                AgentToolConfig.agent_type_id == brainstorm_agent.id,
                AgentToolConfig.tool_id == tool.id,
            )
        )
        config = result.scalar_one_or_none()

        assert config is not None
        assert config.enabled_for_agent is True
        assert config.order_index == 3  # After create_plan=1 and web_search=2
        assert config.usage_limit == 10
        assert config.allow_use is True
        assert config.requires_approval is False

    async def test_tool_assignment_is_idempotent(
        self,
        db_session: AsyncSession,
        brainstorm_agent: AgentType,
        existing_tools: list[Tool],
    ):
        """Test that running assignment twice doesn't create duplicate assignments."""
        from scripts.seed_explore_codebase_tool import (
            seed_explore_codebase_tool,
            assign_tool_to_brainstorm_agent,
        )

        # Create tool and assign twice
        await seed_explore_codebase_tool(db_session)
        await assign_tool_to_brainstorm_agent(db_session)
        await assign_tool_to_brainstorm_agent(db_session)

        # Get the tool
        result = await db_session.execute(
            select(Tool).where(Tool.name == "explore_codebase")
        )
        tool = result.scalar_one()

        # Verify only one assignment exists
        result = await db_session.execute(
            select(AgentToolConfig).where(
                AgentToolConfig.agent_type_id == brainstorm_agent.id,
                AgentToolConfig.tool_id == tool.id,
            )
        )
        configs = result.scalars().all()

        assert len(configs) == 1

    async def test_assignment_skipped_if_no_brainstorm_agent(
        self, db_session: AsyncSession
    ):
        """Test that assignment is skipped gracefully if brainstorm agent doesn't exist."""
        from scripts.seed_explore_codebase_tool import (
            seed_explore_codebase_tool,
            assign_tool_to_brainstorm_agent,
        )

        # Create tool without creating agent first
        await seed_explore_codebase_tool(db_session)

        # This should not raise an exception
        await assign_tool_to_brainstorm_agent(db_session)

        # Verify no assignments were created
        result = await db_session.execute(select(AgentToolConfig))
        configs = result.scalars().all()

        assert len(configs) == 0

    async def test_assignment_skipped_if_tool_not_found(
        self, db_session: AsyncSession, brainstorm_agent: AgentType
    ):
        """Test that assignment is skipped gracefully if tool doesn't exist."""
        from scripts.seed_explore_codebase_tool import assign_tool_to_brainstorm_agent

        # Try to assign without creating the tool first
        await assign_tool_to_brainstorm_agent(db_session)

        # Verify no assignments were created
        result = await db_session.execute(select(AgentToolConfig))
        configs = result.scalars().all()

        assert len(configs) == 0
