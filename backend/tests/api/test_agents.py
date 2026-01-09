"""Tests for agent API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_agents(async_client: AsyncClient, db_session):
    """Test listing available agents."""
    from app.models.agent import AgentType

    # Create test agent
    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        avatar_url="🤖",
        avatar_color="#FF0000",
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=True,
    )
    db_session.add(agent)
    await db_session.commit()

    # List agents
    response = await async_client.get("/api/v1/agents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_agent"
    assert data[0]["display_name"] == "Test Agent"
    assert data[0]["avatar_url"] == "🤖"


@pytest.mark.asyncio
async def test_get_agent_config(async_client: AsyncClient, db_session):
    """Test getting specific agent configuration."""
    from app.models.agent import AgentType

    agent = AgentType(
        name="brainstorm",
        display_name="Claude the Brainstormer",
        description="Creative facilitator",
        avatar_url="🎨",
        avatar_color="#f59e0b",
        personality_traits=["creative", "strategic"],
        model="claude-sonnet-4-5",
        system_prompt="Test",
    )
    db_session.add(agent)
    await db_session.commit()

    response = await async_client.get("/api/v1/agents/brainstorm")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "brainstorm"
    assert data["display_name"] == "Claude the Brainstormer"
    assert "creative" in data["personality_traits"]


@pytest.mark.asyncio
async def test_get_agent_tools(async_client: AsyncClient, db_session):
    """Test getting tools assigned to an agent."""
    from app.models.tool import Tool
    from app.models.agent import AgentType, AgentToolConfig

    # Create tool and agent
    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    # Assign tool
    config = AgentToolConfig(agent_type_id=agent.id, tool_id=tool.id, enabled_for_agent=True)
    db_session.add(config)
    await db_session.commit()

    response = await async_client.get(f"/api/v1/agents/{agent.id}/tools")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_tool"
