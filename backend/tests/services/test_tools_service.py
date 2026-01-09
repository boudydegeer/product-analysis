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


@pytest.mark.asyncio
async def test_check_tool_allowed_disabled(db_session):
    """Test that disabled tools are not allowed."""
    service = ToolsService(db_session)

    tool = Tool(name="disabled_tool", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    # Configure but disable
    config = AgentToolConfig(
        agent_type_id=agent.id,
        tool_id=tool.id,
        enabled_for_agent=False,
        allow_use=True
    )
    db_session.add(config)
    await db_session.commit()

    allowed = await service.check_tool_allowed(agent.id, "disabled_tool")
    assert allowed is False


@pytest.mark.asyncio
async def test_check_tool_allowed_use_not_allowed(db_session):
    """Test that tools with allow_use=False are not allowed."""
    service = ToolsService(db_session)

    tool = Tool(name="restricted_tool", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    # Configure but disallow use
    config = AgentToolConfig(
        agent_type_id=agent.id,
        tool_id=tool.id,
        enabled_for_agent=True,
        allow_use=False
    )
    db_session.add(config)
    await db_session.commit()

    allowed = await service.check_tool_allowed(agent.id, "restricted_tool")
    assert allowed is False


@pytest.mark.asyncio
async def test_get_tool_by_name(db_session):
    """Test getting tool by name."""
    service = ToolsService(db_session)

    tool = Tool(
        name="test_tool",
        description="Test",
        category="test",
        tool_type="builtin",
        definition={"input_schema": {}}
    )
    db_session.add(tool)
    await db_session.commit()

    found_tool = await service.get_tool_by_name("test_tool")
    assert found_tool is not None
    assert found_tool.name == "test_tool"

    not_found = await service.get_tool_by_name("nonexistent")
    assert not_found is None


@pytest.mark.asyncio
async def test_assign_tool_to_agent(db_session):
    """Test assigning tool to agent."""
    service = ToolsService(db_session)

    tool = Tool(name="tool1", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    config = await service.assign_tool_to_agent(
        agent_type_id=agent.id,
        tool_id=tool.id,
        config={"enabled_for_agent": True, "allow_use": True}
    )

    assert config.agent_type_id == agent.id
    assert config.tool_id == tool.id
    assert config.enabled_for_agent is True
    assert config.allow_use is True


@pytest.mark.asyncio
async def test_audit_tool_usage(db_session):
    """Test auditing tool usage."""
    service = ToolsService(db_session)

    tool = Tool(name="audit_tool", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    audit = await service.audit_tool_usage(
        session_id="session123",
        agent_type_id=agent.id,
        tool_name="audit_tool",
        parameters={"param1": "value1"},
        result={"output": "success"},
        status="success",
        execution_time_ms=150
    )

    assert audit.session_id == "session123"
    assert audit.agent_type_id == agent.id
    assert audit.tool_id == tool.id
    assert audit.parameters == {"param1": "value1"}
    assert audit.result == {"output": "success"}
    assert audit.status == "success"
    assert audit.execution_time_ms == 150


@pytest.mark.asyncio
async def test_audit_tool_usage_with_error(db_session):
    """Test auditing failed tool usage."""
    service = ToolsService(db_session)

    tool = Tool(name="error_tool", description="Test", category="test", tool_type="builtin", definition={})
    db_session.add(tool)
    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    audit = await service.audit_tool_usage(
        session_id="session456",
        agent_type_id=agent.id,
        tool_name="error_tool",
        parameters={"param1": "value1"},
        result={},
        status="failed",
        execution_time_ms=50,
        error_message="Tool execution failed"
    )

    assert audit.status == "failed"
    assert audit.error_message == "Tool execution failed"


@pytest.mark.asyncio
async def test_audit_tool_usage_nonexistent_tool(db_session):
    """Test auditing usage of nonexistent tool."""
    service = ToolsService(db_session)

    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    # Should not raise error, tool_id will be None
    audit = await service.audit_tool_usage(
        session_id="session789",
        agent_type_id=agent.id,
        tool_name="nonexistent_tool",
        parameters={},
        result={},
        status="denied",
        execution_time_ms=0
    )

    assert audit.tool_id is None
    assert audit.status == "denied"


@pytest.mark.asyncio
async def test_get_tools_for_agent_ordering(db_session):
    """Test that tools are returned in correct order."""
    service = ToolsService(db_session)

    # Create tools
    tool1 = Tool(name="tool1", description="Tool 1", category="test", tool_type="builtin", definition={})
    tool2 = Tool(name="tool2", description="Tool 2", category="test", tool_type="builtin", definition={})
    tool3 = Tool(name="tool3", description="Tool 3", category="test", tool_type="builtin", definition={})
    db_session.add_all([tool1, tool2, tool3])

    agent = AgentType(name="test_agent", display_name="Test", model="claude-sonnet-4-5", system_prompt="Test")
    db_session.add(agent)
    await db_session.commit()

    # Assign with specific order
    config1 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool1.id, enabled_for_agent=True, order_index=2)
    config2 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool2.id, enabled_for_agent=True, order_index=0)
    config3 = AgentToolConfig(agent_type_id=agent.id, tool_id=tool3.id, enabled_for_agent=True, order_index=1)
    db_session.add_all([config1, config2, config3])
    await db_session.commit()

    tools = await service.get_tools_for_agent(agent.id, enabled_only=True)

    # Should be ordered by order_index: tool2, tool3, tool1
    assert len(tools) == 3
    assert tools[0]["name"] == "tool2"
    assert tools[1]["name"] == "tool3"
    assert tools[2]["name"] == "tool1"


@pytest.mark.asyncio
async def test_tool_to_sdk_format(db_session):
    """Test converting tool to SDK format."""
    service = ToolsService(db_session)

    tool = Tool(
        name="test_tool",
        description="A test tool",
        category="test",
        tool_type="builtin",
        definition={
            "input_schema": {
                "type": "object",
                "properties": {"param1": {"type": "string"}}
            }
        }
    )

    sdk_format = service._tool_to_sdk_format(tool)

    assert sdk_format["name"] == "test_tool"
    assert sdk_format["description"] == "A test tool"
    assert "input_schema" in sdk_format
    assert sdk_format["input_schema"]["properties"]["param1"]["type"] == "string"
