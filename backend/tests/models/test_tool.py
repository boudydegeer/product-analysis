"""Tests for Tool model."""
import pytest
from app.models.tool import Tool


@pytest.mark.asyncio
async def test_create_tool(db_session):
    """Test creating a tool."""
    tool = Tool(
        name="test_tool",
        description="Test tool description",
        category="test",
        tool_type="builtin",
        definition={"input_schema": {"type": "object"}},
    )

    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    assert tool.id is not None
    assert tool.name == "test_tool"
    assert tool.enabled is True
    assert tool.is_dangerous is False


@pytest.mark.asyncio
async def test_tool_unique_name(db_session):
    """Test that tool names must be unique."""
    tool1 = Tool(
        name="duplicate",
        description="First",
        category="test",
        tool_type="builtin",
        definition={},
    )
    db_session.add(tool1)
    await db_session.commit()

    tool2 = Tool(
        name="duplicate",
        description="Second",
        category="test",
        tool_type="builtin",
        definition={},
    )
    db_session.add(tool2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_tool_jsonb_fields(db_session):
    """Test JSONB fields work correctly."""
    tool = Tool(
        name="complex_tool",
        description="Test",
        category="test",
        tool_type="custom",
        definition={
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                }
            }
        },
        tags=["tag1", "tag2"],
    )

    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)

    assert tool.definition["input_schema"]["properties"]["param1"]["type"] == "string"
    assert "tag1" in tool.tags
