"""Tests for AgentFactory."""
import pytest
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService
from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig


@pytest.mark.asyncio
async def test_create_agent_client(db_session, monkeypatch):
    """Test creating an SDK client for an agent."""
    # Mock ClaudeSDKClient to avoid actual API calls
    class MockClaudeSDKClient:
        def __init__(self, options):
            self.options = options

    monkeypatch.setattr(
        "app.services.agent_factory.ClaudeSDKClient",
        MockClaudeSDKClient
    )

    # Setup: Create agent with tools
    tool1 = Tool(name="tool1", description="Tool 1", category="test", tool_type="builtin", definition={"input_schema": {}})
    tool2 = Tool(name="tool2", description="Tool 2", category="test", tool_type="builtin", definition={"input_schema": {}})
    db_session.add_all([tool1, tool2])

    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        model="claude-sonnet-4-5",
        system_prompt="Test prompt",
        temperature=0.8,
        max_context_tokens=150000,
    )
    db_session.add(agent)
    await db_session.commit()

    # Assign tools
    config1 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool1.id, enabled_for_agent=True)
    config2 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool2.id, enabled_for_agent=True)
    db_session.add_all([config1, config2])
    await db_session.commit()

    # Create factory
    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    # Create client
    client = await factory.create_agent_client("test_agent")

    # Verify options
    assert client.options.model == "claude-sonnet-4-5"
    assert client.options.system_prompt == "Test prompt"
    assert len(client.options.tools) == 2

    # Tools are now passed as list of names (strings), not full definitions
    assert "tool1" in client.options.tools
    assert "tool2" in client.options.tools


@pytest.mark.asyncio
async def test_get_agent_config(db_session):
    """Test getting agent configuration."""
    agent = AgentType(
        name="brainstorm",
        display_name="Claude the Brainstormer",
        avatar_url="🎨",
        avatar_color="#f59e0b",
        personality_traits=["creative", "strategic"],
        model="claude-sonnet-4-5",
        system_prompt="You are a brainstormer",
    )
    db_session.add(agent)
    await db_session.commit()

    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    config = await factory.get_agent_config("brainstorm")

    assert config["name"] == "brainstorm"
    assert config["display_name"] == "Claude the Brainstormer"
    assert config["avatar_url"] == "🎨"
    assert config["avatar_color"] == "#f59e0b"
    assert "creative" in config["personality_traits"]


@pytest.mark.asyncio
async def test_create_agent_client_not_found(db_session):
    """Test creating client for non-existent agent raises error."""
    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    with pytest.raises(ValueError, match="Agent type 'nonexistent' not found"):
        await factory.create_agent_client("nonexistent")


@pytest.mark.asyncio
async def test_create_agent_client_disabled(db_session, monkeypatch):
    """Test creating client for disabled agent raises error."""
    class MockClaudeSDKClient:
        def __init__(self, options):
            self.options = options

    monkeypatch.setattr(
        "app.services.agent_factory.ClaudeSDKClient",
        MockClaudeSDKClient
    )

    agent = AgentType(
        name="disabled_agent",
        display_name="Disabled Agent",
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=False,
    )
    db_session.add(agent)
    await db_session.commit()

    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    with pytest.raises(ValueError, match="Agent type 'disabled_agent' is disabled"):
        await factory.create_agent_client("disabled_agent")


@pytest.mark.asyncio
async def test_create_agent_client_no_tools(db_session, monkeypatch):
    """Test creating client for agent with no tools."""
    class MockClaudeSDKClient:
        def __init__(self, options):
            self.options = options

    monkeypatch.setattr(
        "app.services.agent_factory.ClaudeSDKClient",
        MockClaudeSDKClient
    )

    agent = AgentType(
        name="no_tools_agent",
        display_name="No Tools Agent",
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=True,
    )
    db_session.add(agent)
    await db_session.commit()

    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    client = await factory.create_agent_client("no_tools_agent")

    assert client.options.model == "claude-sonnet-4-5"
    assert client.options.tools is None


@pytest.mark.asyncio
async def test_get_agent_config_not_found(db_session):
    """Test getting config for non-existent agent raises error."""
    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    with pytest.raises(ValueError, match="Agent type 'nonexistent' not found"):
        await factory.get_agent_config("nonexistent")


@pytest.mark.asyncio
async def test_list_available_agents(db_session):
    """Test listing all available agents."""
    agent1 = AgentType(
        name="agent1",
        display_name="Agent 1",
        description="First agent",
        avatar_url="🤖",
        avatar_color="#FF0000",
        personality_traits=["helpful"],
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=True,
    )
    agent2 = AgentType(
        name="agent2",
        display_name="Agent 2",
        description="Second agent",
        avatar_url="🎨",
        avatar_color="#00FF00",
        personality_traits=["creative"],
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=True,
    )
    agent3 = AgentType(
        name="agent3",
        display_name="Agent 3",
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=False,
    )
    db_session.add_all([agent1, agent2, agent3])
    await db_session.commit()

    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    # Test enabled only (default)
    agents = await factory.list_available_agents(enabled_only=True)
    assert len(agents) == 2
    agent_names = [a["name"] for a in agents]
    assert "agent1" in agent_names
    assert "agent2" in agent_names
    assert "agent3" not in agent_names

    # Test all agents
    all_agents = await factory.list_available_agents(enabled_only=False)
    assert len(all_agents) == 3


@pytest.mark.asyncio
async def test_list_available_agents_returns_correct_fields(db_session):
    """Test that list_available_agents returns correct fields."""
    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        description="Test description",
        avatar_url="🤖",
        avatar_color="#FF0000",
        personality_traits=["helpful", "creative"],
        model="claude-sonnet-4-5",
        system_prompt="Test",
        enabled=True,
    )
    db_session.add(agent)
    await db_session.commit()

    tools_service = ToolsService(db_session)
    factory = AgentFactory(db_session, tools_service)

    agents = await factory.list_available_agents()
    assert len(agents) == 1

    agent_data = agents[0]
    assert agent_data["id"] == agent.id
    assert agent_data["name"] == "test_agent"
    assert agent_data["display_name"] == "Test Agent"
    assert agent_data["description"] == "Test description"
    assert agent_data["avatar_url"] == "🤖"
    assert agent_data["avatar_color"] == "#FF0000"
    assert agent_data["personality_traits"] == ["helpful", "creative"]
