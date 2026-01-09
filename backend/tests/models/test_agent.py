"""Tests for Agent models."""
import pytest
from app.models.agent import AgentType, AgentToolConfig


@pytest.mark.asyncio
async def test_create_agent_type(db_session):
    """Test creating an agent type."""
    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        description="Test agent description",
        avatar_url="🤖",
        avatar_color="#FF0000",
        personality_traits=["helpful", "precise"],
        model="claude-sonnet-4-5",
        system_prompt="You are a test agent",
        temperature=0.5,
    )

    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    assert agent.id is not None
    assert agent.name == "test_agent"
    assert agent.display_name == "Test Agent"
    assert agent.avatar_url == "🤖"
    assert agent.avatar_color == "#FF0000"
    assert "helpful" in agent.personality_traits
    assert agent.temperature == 0.5


@pytest.mark.asyncio
async def test_agent_tool_config_relationship(db_session):
    """Test agent-tool relationship through config."""
    from app.models.tool import Tool
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Create tool
    tool = Tool(
        name="test_tool",
        description="Test",
        category="test",
        tool_type="builtin",
        definition={},
    )
    db_session.add(tool)

    # Create agent
    agent = AgentType(
        name="test_agent",
        display_name="Test",
        model="claude-sonnet-4-5",
        system_prompt="Test",
    )
    db_session.add(agent)
    await db_session.commit()

    # Link them
    config = AgentToolConfig(
        agent_type_id=agent.id,
        tool_id=tool.id,
        enabled_for_agent=True,
        usage_limit=10,
    )
    db_session.add(config)
    await db_session.commit()

    # Reload agent with eager loading
    result = await db_session.execute(
        select(AgentType)
        .where(AgentType.id == agent.id)
        .options(selectinload(AgentType.tool_configs).selectinload(AgentToolConfig.tool))
    )
    agent = result.scalar_one()

    assert len(agent.tool_configs) == 1
    assert agent.tool_configs[0].tool.name == "test_tool"
    assert agent.tool_configs[0].usage_limit == 10
