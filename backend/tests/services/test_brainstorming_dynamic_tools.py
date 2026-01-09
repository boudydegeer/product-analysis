"""Tests for BrainstormingService with dynamic tools."""
import pytest
from app.services.brainstorming_service import BrainstormingService
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService
from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig


@pytest.mark.asyncio
async def test_service_uses_agent_config(db_session, monkeypatch):
    """Test that service loads agent config from database."""
    # Mock SDK client
    class MockClaudeSDKClient:
        def __init__(self, options):
            self.options = options
            self.connected = False

        async def connect(self):
            self.connected = True

        async def disconnect(self):
            self.connected = False

    monkeypatch.setattr(
        "app.services.agent_factory.ClaudeSDKClient",
        MockClaudeSDKClient
    )

    # Setup: Create agent with custom config
    tool = Tool(name="test_tool", description="Test", category="test", tool_type="builtin", definition={"input_schema": {}})
    db_session.add(tool)

    agent = AgentType(
        name="brainstorm",
        display_name="Claude the Brainstormer",
        model="claude-sonnet-4-5",
        system_prompt="Custom prompt for testing",
        temperature=0.9,
    )
    db_session.add(agent)
    await db_session.commit()

    config = AgentToolConfig(agent_type_id=agent.id, tool_id=tool.id, enabled_for_agent=True)
    db_session.add(config)
    await db_session.commit()

    # Create service
    tools_service = ToolsService(db_session)
    agent_factory = AgentFactory(db_session, tools_service)

    service = BrainstormingService(
        api_key="test-key",
        agent_factory=agent_factory,
        agent_name="brainstorm"
    )

    await service._ensure_connected()

    # Verify client was initialized with agent config
    assert service.client is not None
    assert service.client.options.model == "claude-sonnet-4-5"
    assert service.client.options.system_prompt == "Custom prompt for testing"
    assert len(service.client.options.tools) == 1
