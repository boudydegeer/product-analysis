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


@pytest.mark.asyncio
async def test_get_agent_config_not_found(async_client: AsyncClient, db_session):
    """Test getting config for non-existent agent returns 404."""
    response = await async_client.get("/api/v1/agents/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_list_agents_empty(async_client: AsyncClient, db_session):
    """Test listing agents when none exist."""
    response = await async_client.get("/api/v1/agents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_agents_disabled_filter(async_client: AsyncClient, db_session):
    """Test listing agents with enabled_only filter."""
    from app.models.agent import AgentType

    enabled_agent = AgentType(
        name="enabled",
        display_name="Enabled",
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=True,
    )
    disabled_agent = AgentType(
        name="disabled",
        display_name="Disabled",
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=False,
    )
    db_session.add_all([enabled_agent, disabled_agent])
    await db_session.commit()

    # Test enabled only (default)
    response = await async_client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "enabled"

    # Test all agents
    response = await async_client.get("/api/v1/agents?enabled_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_agent_tools_no_tools(async_client: AsyncClient, db_session):
    """Test getting tools for agent with no assigned tools."""
    from app.models.agent import AgentType

    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    response = await async_client.get(f"/api/v1/agents/{agent.id}/tools")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_agent_tools_disabled_filter(async_client: AsyncClient, db_session):
    """Test getting tools with enabled_only filter."""
    from app.models.tool import Tool
    from app.models.agent import AgentType, AgentToolConfig

    tool1 = Tool(name="enabled_tool", description="Enabled", category="test", tool_type="builtin", definition={})
    tool2 = Tool(name="disabled_tool", description="Disabled", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool1, tool2, agent])
    await db_session.commit()

    config1 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool1.id, enabled_for_agent=True)
    config2 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool2.id, enabled_for_agent=False)
    db_session.add_all([config1, config2])
    await db_session.commit()

    # Test enabled only (default)
    response = await async_client.get(f"/api/v1/agents/{agent.id}/tools")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "enabled_tool"

    # Test all tools
    response = await async_client.get(f"/api/v1/agents/{agent.id}/tools?enabled_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
