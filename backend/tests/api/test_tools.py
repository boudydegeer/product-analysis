"""Tests for tools API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tool(async_client: AsyncClient, db_session):
    """Test creating a new tool."""
    tool_data = {
        "name": "test_tool",
        "description": "A test tool for testing",
        "category": "testing",
        "tool_type": "custom",
        "definition": {
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        },
        "enabled": True,
        "is_dangerous": False,
        "requires_approval": False,
        "version": "1.0.0",
        "tags": ["test", "demo"],
        "example_usage": "Example: use test_tool with param1='value'",
        "created_by": "test_user"
    }

    response = await async_client.post("/api/v1/tools", json=tool_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_tool"
    assert data["description"] == "A test tool for testing"
    assert data["category"] == "testing"
    assert data["tool_type"] == "custom"
    assert data["enabled"] is True
    assert data["is_dangerous"] is False
    assert data["requires_approval"] is False
    assert data["version"] == "1.0.0"
    assert data["tags"] == ["test", "demo"]
    assert data["example_usage"] == "Example: use test_tool with param1='value'"
    assert data["created_by"] == "test_user"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_tool_duplicate_name(async_client: AsyncClient, db_session):
    """Test creating a tool with duplicate name returns 409."""
    from app.models.tool import Tool

    # Create existing tool
    tool = Tool(
        name="duplicate_tool",
        description="First tool",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    db_session.add(tool)
    await db_session.commit()

    # Try to create duplicate
    tool_data = {
        "name": "duplicate_tool",
        "description": "Second tool",
        "category": "test",
        "tool_type": "custom",
        "definition": {"input_schema": {"type": "object"}},
    }

    response = await async_client.post("/api/v1/tools", json=tool_data)

    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_create_tool_invalid_definition(async_client: AsyncClient, db_session):
    """Test creating a tool with invalid definition returns 422."""
    tool_data = {
        "name": "invalid_tool",
        "description": "Tool with invalid definition",
        "category": "test",
        "tool_type": "custom",
        "definition": {},  # Missing input_schema/parameters
    }

    response = await async_client.post("/api/v1/tools", json=tool_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_tool_invalid_tool_type(async_client: AsyncClient, db_session):
    """Test creating a tool with invalid tool_type returns 422."""
    tool_data = {
        "name": "invalid_type_tool",
        "description": "Tool with invalid type",
        "category": "test",
        "tool_type": "invalid_type",
        "definition": {"input_schema": {"type": "object"}},
    }

    response = await async_client.post("/api/v1/tools", json=tool_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_tools(async_client: AsyncClient, db_session):
    """Test listing all tools."""
    from app.models.tool import Tool

    # Create test tools
    tools = [
        Tool(
            name="tool1",
            description="First tool",
            category="category1",
            tool_type="builtin",
            definition={"input_schema": {"type": "object"}},
            enabled=True,
        ),
        Tool(
            name="tool2",
            description="Second tool",
            category="category2",
            tool_type="custom",
            definition={"input_schema": {"type": "object"}},
            enabled=True,
        ),
        Tool(
            name="tool3",
            description="Third tool",
            category="category1",
            tool_type="mcp",
            definition={"input_schema": {"type": "object"}},
            enabled=False,
        ),
    ]
    db_session.add_all(tools)
    await db_session.commit()

    # List all enabled tools (default)
    response = await async_client.get("/api/v1/tools")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Only enabled tools
    assert all(tool["enabled"] for tool in data)


@pytest.mark.asyncio
async def test_list_tools_with_filters(async_client: AsyncClient, db_session):
    """Test listing tools with filters."""
    from app.models.tool import Tool

    # Create test tools
    tools = [
        Tool(
            name="tool1",
            description="First tool",
            category="category1",
            tool_type="builtin",
            definition={"input_schema": {"type": "object"}},
            enabled=True,
        ),
        Tool(
            name="tool2",
            description="Second tool",
            category="category2",
            tool_type="custom",
            definition={"input_schema": {"type": "object"}},
            enabled=True,
        ),
        Tool(
            name="tool3",
            description="Third tool",
            category="category1",
            tool_type="mcp",
            definition={"input_schema": {"type": "object"}},
            enabled=False,
        ),
    ]
    db_session.add_all(tools)
    await db_session.commit()

    # Filter by category
    response = await async_client.get("/api/v1/tools?category=category1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Only tool1 (tool3 is disabled)
    assert data[0]["name"] == "tool1"

    # Filter by tool_type
    response = await async_client.get("/api/v1/tools?tool_type=custom")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "tool2"

    # Show all tools (including disabled)
    response = await async_client.get("/api/v1/tools?enabled_only=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


@pytest.mark.asyncio
async def test_list_tools_pagination(async_client: AsyncClient, db_session):
    """Test listing tools with pagination."""
    from app.models.tool import Tool

    # Create 5 test tools
    tools = [
        Tool(
            name=f"tool{i}",
            description=f"Tool {i}",
            category="test",
            tool_type="custom",
            definition={"input_schema": {"type": "object"}},
            enabled=True,
        )
        for i in range(5)
    ]
    db_session.add_all(tools)
    await db_session.commit()

    # Get first 2
    response = await async_client.get("/api/v1/tools?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Get next 2
    response = await async_client.get("/api/v1/tools?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_tools_empty(async_client: AsyncClient, db_session):
    """Test listing tools when none exist."""
    response = await async_client.get("/api/v1/tools")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_tool(async_client: AsyncClient, db_session):
    """Test getting a specific tool."""
    from app.models.tool import Tool

    tool = Tool(
        name="get_test_tool",
        description="Tool for get test",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
        tags=["test"],
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    response = await async_client.get(f"/api/v1/tools/{tool.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tool.id
    assert data["name"] == "get_test_tool"
    assert data["description"] == "Tool for get test"
    assert data["tags"] == ["test"]


@pytest.mark.asyncio
async def test_get_tool_not_found(async_client: AsyncClient, db_session):
    """Test getting non-existent tool returns 404."""
    response = await async_client.get("/api/v1/tools/99999")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_tool(async_client: AsyncClient, db_session):
    """Test updating a tool."""
    from app.models.tool import Tool

    tool = Tool(
        name="update_test_tool",
        description="Original description",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
        enabled=True,
        version="1.0.0",
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    update_data = {
        "description": "Updated description",
        "enabled": False,
        "version": "2.0.0",
        "tags": ["updated"],
    }

    response = await async_client.put(f"/api/v1/tools/{tool.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tool.id
    assert data["name"] == "update_test_tool"  # Unchanged
    assert data["description"] == "Updated description"
    assert data["enabled"] is False
    assert data["version"] == "2.0.0"
    assert data["tags"] == ["updated"]


@pytest.mark.asyncio
async def test_update_tool_name(async_client: AsyncClient, db_session):
    """Test updating a tool's name."""
    from app.models.tool import Tool

    tool = Tool(
        name="original_name",
        description="Test tool",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    update_data = {"name": "new_name"}

    response = await async_client.put(f"/api/v1/tools/{tool.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new_name"


@pytest.mark.asyncio
async def test_update_tool_duplicate_name(async_client: AsyncClient, db_session):
    """Test updating a tool to duplicate name returns 409."""
    from app.models.tool import Tool

    tool1 = Tool(
        name="tool1",
        description="First tool",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    tool2 = Tool(
        name="tool2",
        description="Second tool",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    db_session.add_all([tool1, tool2])
    await db_session.commit()
    await db_session.refresh(tool2)

    # Try to rename tool2 to tool1
    update_data = {"name": "tool1"}

    response = await async_client.put(f"/api/v1/tools/{tool2.id}", json=update_data)

    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]


@pytest.mark.asyncio
async def test_update_tool_not_found(async_client: AsyncClient, db_session):
    """Test updating non-existent tool returns 404."""
    update_data = {"description": "Updated"}

    response = await async_client.put("/api/v1/tools/99999", json=update_data)

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_update_tool_invalid_definition(async_client: AsyncClient, db_session):
    """Test updating tool with invalid definition returns 422."""
    from app.models.tool import Tool

    tool = Tool(
        name="test_tool",
        description="Test tool",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    update_data = {"definition": {}}  # Invalid - missing input_schema

    response = await async_client.put(f"/api/v1/tools/{tool.id}", json=update_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_tool(async_client: AsyncClient, db_session):
    """Test deleting a tool."""
    from app.models.tool import Tool

    tool = Tool(
        name="delete_test_tool",
        description="Tool to be deleted",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    response = await async_client.delete(f"/api/v1/tools/{tool.id}")

    assert response.status_code == 204

    # Verify tool is deleted
    response = await async_client.get(f"/api/v1/tools/{tool.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_tool_not_found(async_client: AsyncClient, db_session):
    """Test deleting non-existent tool returns 404."""
    response = await async_client.delete("/api/v1/tools/99999")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_tool_with_parameters_instead_of_input_schema(
    async_client: AsyncClient, db_session
):
    """Test creating a tool with 'parameters' instead of 'input_schema'."""
    tool_data = {
        "name": "param_tool",
        "description": "Tool using parameters",
        "category": "test",
        "tool_type": "custom",
        "definition": {
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        },
    }

    response = await async_client.post("/api/v1/tools", json=tool_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "param_tool"
    assert "parameters" in data["definition"]


@pytest.mark.asyncio
async def test_tool_cascade_delete_with_agent_configs(
    async_client: AsyncClient, db_session
):
    """Test that deleting a tool cascades to agent_tool_configs."""
    from app.models.tool import Tool
    from app.models.agent import AgentType, AgentToolConfig

    # Create tool and agent
    tool = Tool(
        name="cascade_test_tool",
        description="Tool for cascade test",
        category="test",
        tool_type="custom",
        definition={"input_schema": {"type": "object"}},
    )
    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        model="claude-sonnet-4-5",
        system_prompt="Test prompt",
    )
    db_session.add_all([tool, agent])
    await db_session.commit()
    await db_session.refresh(tool)
    await db_session.refresh(agent)

    # Create agent-tool config
    config = AgentToolConfig(
        agent_type_id=agent.id,
        tool_id=tool.id,
        enabled_for_agent=True,
    )
    db_session.add(config)
    await db_session.commit()

    # Delete tool
    response = await async_client.delete(f"/api/v1/tools/{tool.id}")
    assert response.status_code == 204

    # Verify config was also deleted (cascade)
    from sqlalchemy import select
    result = await db_session.execute(
        select(AgentToolConfig).where(AgentToolConfig.tool_id == tool.id)
    )
    configs = result.scalars().all()
    assert len(configs) == 0
