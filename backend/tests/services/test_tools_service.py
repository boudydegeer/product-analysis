"""Tests for ToolsService."""
import pytest
from app.services.tools_service import ToolsService
from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig


@pytest.mark.asyncio
async def test_get_tools_for_agent(db_session):
    """Test getting tools assigned to an agent."""
    service = ToolsService(db_session)

    # Create tools
    tool1 = Tool(name="tool1", description="Tool 1", category="test", tool_type="builtin", definition={})
    tool2 = Tool(name="tool2", description="Tool 2", category="test", tool_type="builtin", definition={})
    tool3 = Tool(name="tool3", description="Tool 3", category="test", tool_type="builtin", definition={})
    db_session.add_all([tool1, tool2, tool3])

    # Create agent
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    # Assign only tool1 and tool2 to agent
    config1 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool1.id, enabled_for_agent=True)
    config2 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool2.id, enabled_for_agent=True)
    config3 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool3.id, enabled_for_agent=False)  # Disabled
    db_session.add_all([config1, config2, config3])
    await db_session.commit()

    # Get tools
    tools = await service.get_tools_for_agent(agent.id, enabled_only=True)

    assert len(tools) == 2
    tool_names = [t["name"] for t in tools]
    assert "tool1" in tool_names
    assert "tool2" in tool_names
    assert "tool3" not in tool_names


@pytest.mark.asyncio
async def test_register_tool(db_session):
    """Test registering a new tool."""
    service = ToolsService(db_session)

    tool_def = {
        "name": "test_tool",
        "description": "A test tool",
        "category": "test",
        "tool_type": "custom",
        "definition": {
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        },
        "is_dangerous": False,
    }

    tool = await service.register_tool(tool_def)

    assert tool.id is not None
    assert tool.name == "test_tool"
    assert tool.definition["input_schema"]["properties"]["param1"]["type"] == "string"


@pytest.mark.asyncio
async def test_check_tool_allowed(db_session):
    """Test checking if tool is allowed for agent."""
    service = ToolsService(db_session)

    # Setup
    tool = Tool(name="allowed_tool", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    # Not configured = not allowed
    allowed = await service.check_tool_allowed(agent.id, "allowed_tool")
    assert allowed is False

    # Configure and enable
    config = AgentToolConfig(agent_type_id=agent.id, tool_id=tool.id, enabled_for_agent=True, allow_use=True)
    db_session.add(config)
    await db_session.commit()

    allowed = await service.check_tool_allowed(agent.id, "allowed_tool")
    assert allowed is True
