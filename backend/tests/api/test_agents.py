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


@pytest.mark.asyncio
async def test_create_agent(async_client: AsyncClient, db_session):
    """Test creating a new agent."""
    agent_data = {
        "name": "new_agent",
        "display_name": "New Agent",
        "description": "A new test agent",
        "avatar_url": "https://example.com/avatar.png",
        "avatar_color": "#FF0000",
        "personality_traits": ["helpful", "creative"],
        "model": "claude-sonnet-4-5",
        "system_prompt": "You are a helpful agent",
        "streaming_enabled": True,
        "max_context_tokens": 100000,
        "temperature": 0.8,
        "enabled": True,
        "is_default": False,
        "version": "1.0.0"
    }

    response = await async_client.post("/api/v1/agents", json=agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "new_agent"
    assert data["display_name"] == "New Agent"
    assert data["description"] == "A new test agent"
    assert data["avatar_color"] == "#FF0000"
    assert "helpful" in data["personality_traits"]
    assert data["model"] == "claude-sonnet-4-5"
    assert data["temperature"] == 0.8
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_agent_duplicate_name(async_client: AsyncClient, db_session):
    """Test creating agent with duplicate name returns 409."""
    from app.models.agent import AgentType

    # Create existing agent
    existing = AgentType(
        name="existing_agent",
        display_name="Existing",
        model="claude-sonnet-4-5",
        system_prompt="Test"
    )
    db_session.add(existing)
    await db_session.commit()

    # Try to create with same name
    agent_data = {
        "name": "existing_agent",
        "display_name": "New Agent",
        "model": "claude-sonnet-4-5",
        "system_prompt": "Test"
    }

    response = await async_client.post("/api/v1/agents", json=agent_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_agent_minimal_fields(async_client: AsyncClient, db_session):
    """Test creating agent with only required fields."""
    agent_data = {
        "name": "minimal_agent",
        "display_name": "Minimal Agent",
        "model": "claude-sonnet-4-5",
        "system_prompt": "You are an agent"
    }

    response = await async_client.post("/api/v1/agents", json=agent_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "minimal_agent"
    assert data["avatar_color"] == "#6366f1"  # Default color
    assert data["personality_traits"] == []  # Default empty list
    assert data["streaming_enabled"] is True  # Default
    assert data["max_context_tokens"] == 200000  # Default


@pytest.mark.asyncio
async def test_update_agent(async_client: AsyncClient, db_session):
    """Test updating an existing agent."""
    from app.models.agent import AgentType

    # Create agent
    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        model="claude-sonnet-4-5",
        system_prompt="Old prompt",
        temperature=0.7
    )
    db_session.add(agent)
    await db_session.commit()

    # Update agent
    update_data = {
        "display_name": "Updated Agent",
        "system_prompt": "New prompt",
        "temperature": 0.9,
        "personality_traits": ["updated"]
    }

    response = await async_client.put(f"/api/v1/agents/{agent.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Updated Agent"
    assert data["system_prompt"] == "New prompt"
    assert data["temperature"] == 0.9
    assert "updated" in data["personality_traits"]
    assert data["name"] == "test_agent"  # Unchanged


@pytest.mark.asyncio
async def test_update_agent_not_found(async_client: AsyncClient, db_session):
    """Test updating non-existent agent returns 404."""
    update_data = {"display_name": "Updated"}

    response = await async_client.put("/api/v1/agents/999", json=update_data)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_agent_duplicate_name(async_client: AsyncClient, db_session):
    """Test updating agent name to duplicate returns 409."""
    from app.models.agent import AgentType

    agent1 = AgentType(name="agent1", display_name="Agent 1", model="claude-sonnet-4-5", system_prompt="Test")
    agent2 = AgentType(name="agent2", display_name="Agent 2", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([agent1, agent2])
    await db_session.commit()

    # Try to rename agent2 to agent1
    update_data = {"name": "agent1"}

    response = await async_client.put(f"/api/v1/agents/{agent2.id}", json=update_data)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_agent(async_client: AsyncClient, db_session):
    """Test deleting an agent."""
    from app.models.agent import AgentType

    agent = AgentType(name="to_delete", display_name="Delete Me", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()
    agent_id = agent.id

    response = await async_client.delete(f"/api/v1/agents/{agent_id}")

    assert response.status_code == 204

    # Verify deleted
    from sqlalchemy import select
    result = await db_session.execute(select(AgentType).where(AgentType.id == agent_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_agent_not_found(async_client: AsyncClient, db_session):
    """Test deleting non-existent agent returns 404."""
    response = await async_client.delete("/api/v1/agents/999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_agent_cascades_tool_configs(async_client: AsyncClient, db_session):
    """Test deleting agent cascades to tool configs."""
    from app.models.agent import AgentType, AgentToolConfig
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    config = AgentToolConfig(agent_type_id=agent.id, tool_id=tool.id, enabled_for_agent=True)
    db_session.add(config)
    await db_session.commit()
    agent_id = agent.id

    response = await async_client.delete(f"/api/v1/agents/{agent_id}")

    assert response.status_code == 204

    # Verify config deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentToolConfig).where(AgentToolConfig.agent_type_id == agent_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_assign_tool_to_agent(async_client: AsyncClient, db_session):
    """Test assigning a tool to an agent."""
    from app.models.agent import AgentType
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    config_data = {
        "enabled_for_agent": True,
        "order_index": 1,
        "allow_use": True,
        "requires_approval": False,
        "usage_limit": 10
    }

    response = await async_client.post(
        f"/api/v1/agents/{agent.id}/tools/{tool.id}",
        json=config_data
    )

    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert data["agent_id"] == agent.id
    assert data["tool_id"] == tool.id


@pytest.mark.asyncio
async def test_assign_tool_to_agent_default_config(async_client: AsyncClient, db_session):
    """Test assigning tool with default configuration."""
    from app.models.agent import AgentType
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    response = await async_client.post(
        f"/api/v1/agents/{agent.id}/tools/{tool.id}",
        json={}
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_assign_tool_agent_not_found(async_client: AsyncClient, db_session):
    """Test assigning tool to non-existent agent returns 404."""
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    await db_session.commit()

    response = await async_client.post(f"/api/v1/agents/999/tools/{tool.id}", json={})

    assert response.status_code == 404
    assert "Agent" in response.json()["detail"]


@pytest.mark.asyncio
async def test_assign_tool_tool_not_found(async_client: AsyncClient, db_session):
    """Test assigning non-existent tool returns 404."""
    from app.models.agent import AgentType

    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    response = await async_client.post(f"/api/v1/agents/{agent.id}/tools/999", json={})

    assert response.status_code == 404
    assert "Tool" in response.json()["detail"]


@pytest.mark.asyncio
async def test_assign_tool_duplicate(async_client: AsyncClient, db_session):
    """Test assigning same tool twice returns 409."""
    from app.models.agent import AgentType, AgentToolConfig
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    # First assignment
    config = AgentToolConfig(agent_type_id=agent.id, tool_id=tool.id, enabled_for_agent=True)
    db_session.add(config)
    await db_session.commit()

    # Try duplicate
    response = await async_client.post(f"/api/v1/agents/{agent.id}/tools/{tool.id}", json={})

    assert response.status_code == 409
    assert "already assigned" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remove_tool_from_agent(async_client: AsyncClient, db_session):
    """Test removing a tool from an agent."""
    from app.models.agent import AgentType, AgentToolConfig
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    config = AgentToolConfig(agent_type_id=agent.id, tool_id=tool.id, enabled_for_agent=True)
    db_session.add(config)
    await db_session.commit()

    response = await async_client.delete(f"/api/v1/agents/{agent.id}/tools/{tool.id}")

    assert response.status_code == 204

    # Verify removed
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_type_id == agent.id,
            AgentToolConfig.tool_id == tool.id
        )
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_remove_tool_not_assigned(async_client: AsyncClient, db_session):
    """Test removing unassigned tool returns 404."""
    from app.models.agent import AgentType
    from app.models.tool import Tool

    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={})
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add_all([tool, agent])
    await db_session.commit()

    response = await async_client.delete(f"/api/v1/agents/{agent.id}/tools/{tool.id}")

    assert response.status_code == 404
    assert "not assigned" in response.json()["detail"]
