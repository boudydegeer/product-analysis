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

    tool_names = [t["name"] for t in client.options.tools]
    assert "tool1" in tool_names
    assert "tool2" in tool_names


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
