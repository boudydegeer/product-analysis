# Dynamic Tools System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Build a database-driven system for managing Claude Agent SDK tools and personalized agents with dynamic tool assignment, enabling different agent types (Brainstorm, Analysis) with custom avatars, personalities, and tool sets.

**Architecture:** Database-first approach with 4 normalized tables (tools, agent_types, agent_tool_configs, tool_usage_audit). Services layer (ToolsService, AgentFactory) handles dynamic tool loading and SDK client initialization. RESTful API exposes CRUD operations. Frontend displays agent personalization and allows agent selection.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, Claude Agent SDK, Vue 3, TypeScript, Pinia

---

## Phase 1: Database Schema & Models

### Task 1: Create Database Migration for Core Tables

**Files:**
- Create: `backend/alembic/versions/XXXX_add_dynamic_tools_tables.py`

**Step 1: Generate migration file**

```bash
cd backend
poetry run alembic revision -m "add dynamic tools tables"
```

Expected: New migration file created in `backend/alembic/versions/`

**Step 2: Write migration - tools table**

In the generated migration file:

```python
"""add dynamic tools tables

Revision ID: XXXX
Revises: <previous_revision>
Create Date: 2026-01-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = 'XXXX'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tools table
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('tool_type', sa.String(50), nullable=False),
        sa.Column('definition', JSONB, nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('is_dangerous', sa.Boolean(), default=False),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('version', sa.String(20), default='1.0.0'),
        sa.Column('tags', JSONB, default='[]'),
        sa.Column('example_usage', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
    )
    op.create_index('idx_tools_category', 'tools', ['category'])
    op.create_index('idx_tools_enabled', 'tools', ['enabled'])

    # Agent types table
    op.create_table(
        'agent_types',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('avatar_color', sa.String(7), default='#6366f1'),
        sa.Column('personality_traits', JSONB, default='[]'),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('streaming_enabled', sa.Boolean(), default=True),
        sa.Column('max_context_tokens', sa.Integer(), default=200000),
        sa.Column('temperature', sa.Float(), default=0.7),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('version', sa.String(20), default='1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_agent_types_enabled', 'agent_types', ['enabled'])

    # Agent tool configs (junction table)
    op.create_table(
        'agent_tool_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('agent_type_id', sa.Integer(), sa.ForeignKey('agent_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_id', sa.Integer(), sa.ForeignKey('tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enabled_for_agent', sa.Boolean(), default=True),
        sa.Column('order_index', sa.Integer()),
        sa.Column('allow_use', sa.Boolean(), default=True),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('usage_limit', sa.Integer()),
        sa.Column('allowed_parameters', JSONB),
        sa.Column('denied_parameters', JSONB),
        sa.Column('parameter_defaults', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint('uq_agent_tool', 'agent_tool_configs', ['agent_type_id', 'tool_id'])
    op.create_index('idx_agent_tool_configs_agent', 'agent_tool_configs', ['agent_type_id'])
    op.create_index('idx_agent_tool_configs_enabled', 'agent_tool_configs', ['enabled_for_agent'])

    # Tool usage audit
    op.create_table(
        'tool_usage_audit',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('session_id', sa.String(50)),
        sa.Column('agent_type_id', sa.Integer(), sa.ForeignKey('agent_types.id'), nullable=True),
        sa.Column('tool_id', sa.Integer(), sa.ForeignKey('tools.id'), nullable=True),
        sa.Column('parameters', JSONB),
        sa.Column('result', JSONB),
        sa.Column('status', sa.String(50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_id', sa.String(255)),
    )
    op.create_index('idx_audit_session', 'tool_usage_audit', ['session_id'])
    op.create_index('idx_audit_created', 'tool_usage_audit', ['created_at'])


def downgrade() -> None:
    op.drop_table('tool_usage_audit')
    op.drop_table('agent_tool_configs')
    op.drop_table('agent_types')
    op.drop_table('tools')
```

**Step 3: Run migration**

```bash
poetry run alembic upgrade head
```

Expected: SUCCESS - All 4 tables created

**Step 4: Verify tables exist**

```bash
docker exec -it postgres-dev psql -U postgres -d product_analysis -c "\dt"
```

Expected: See tools, agent_types, agent_tool_configs, tool_usage_audit tables

**Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: add database tables for dynamic tools system

- Add tools table for tool definitions
- Add agent_types table with personalization fields
- Add agent_tool_configs junction table
- Add tool_usage_audit for tracking"
```

---

### Task 2: Create SQLAlchemy Models

**Files:**
- Create: `backend/app/models/tool.py`
- Create: `backend/app/models/agent.py`

**Step 1: Write test for Tool model**

Create: `backend/tests/models/test_tool.py`

```python
"""Tests for Tool model."""
import pytest
from sqlalchemy import select
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
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/models/test_tool.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.tool'"

**Step 3: Create Tool model**

Create: `backend/app/models/tool.py`

```python
"""Tool model for dynamic tool management."""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Tool(Base):
    """Tool definition for Claude Agent SDK."""

    __tablename__ = "tools"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)

    # Tool Definition
    tool_type: Mapped[str] = mapped_column(String(50), nullable=False)  # builtin | custom | mcp
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dangerous: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    example_usage: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    agent_configs: Mapped[list["AgentToolConfig"]] = relationship(
        "AgentToolConfig", back_populates="tool", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_tools_category", "category"),
        Index("idx_tools_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<Tool(id={self.id}, name='{self.name}', category='{self.category}')>"
```

**Step 4: Write test for AgentType model**

Create: `backend/tests/models/test_agent.py`

```python
"""Tests for Agent models."""
import pytest
from app.models.agent import AgentType, AgentToolConfig


@pytest.mark.asyncio
async def test_create_agent_type(db_session):
    """Test creating an agent type."""
    agent = AgentType(
        name="test_agent",
        display_name="Test Agent",
        description="Test agent description",
        avatar_url="🤖",
        avatar_color="#FF0000",
        personality_traits=["helpful", "precise"],
        model="claude-sonnet-4-5",
        system_prompt="You are a test agent",
        temperature=0.5,
    )

    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)

    assert agent.id is not None
    assert agent.name == "test_agent"
    assert agent.display_name == "Test Agent"
    assert agent.avatar_url == "🤖"
    assert agent.avatar_color == "#FF0000"
    assert "helpful" in agent.personality_traits
    assert agent.temperature == 0.5


@pytest.mark.asyncio
async def test_agent_tool_config_relationship(db_session):
    """Test agent-tool relationship through config."""
    from app.models.tool import Tool

    # Create tool
    tool = Tool(
        name="test_tool",
        description="Test",
        category="test",
        tool_type="builtin",
        definition={},
    )
    db_session.add(tool)

    # Create agent
    agent = AgentType(
        name="test_agent",
        display_name="Test",
        model="claude-sonnet-4-5",
        system_prompt="Test",
    )
    db_session.add(agent)
    await db_session.commit()

    # Link them
    config = AgentToolConfig(
        agent_type_id=agent.id,
        tool_id=tool.id,
        enabled_for_agent=True,
        usage_limit=10,
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(agent)

    assert len(agent.tool_configs) == 1
    assert agent.tool_configs[0].tool.name == "test_tool"
    assert agent.tool_configs[0].usage_limit == 10
```

**Step 5: Run test to verify it fails**

```bash
poetry run pytest backend/tests/models/test_agent.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.agent'"

**Step 6: Create Agent models**

Create: `backend/app/models/agent.py`

```python
"""Agent models for dynamic agent management."""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AgentType(Base):
    """Agent type configuration with personalization."""

    __tablename__ = "agent_types"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identity
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Personalization
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    personality_traits: Mapped[list] = mapped_column(JSONB, default=list)

    # Configuration
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Behavior
    streaming_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_context_tokens: Mapped[int] = mapped_column(Integer, default=200000)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    tool_configs: Mapped[list["AgentToolConfig"]] = relationship(
        "AgentToolConfig", back_populates="agent_type", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_agent_types_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<AgentType(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class AgentToolConfig(Base):
    """Junction table mapping tools to agents with configuration."""

    __tablename__ = "agent_tool_configs"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign Keys
    agent_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent_types.id", ondelete="CASCADE"), nullable=False
    )
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False
    )

    # Configuration
    enabled_for_agent: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Security
    allow_use: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Constraints
    allowed_parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    denied_parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    parameter_defaults: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    agent_type: Mapped["AgentType"] = relationship("AgentType", back_populates="tool_configs")
    tool: Mapped["Tool"] = relationship("Tool", back_populates="agent_configs")

    __table_args__ = (
        UniqueConstraint("agent_type_id", "tool_id", name="uq_agent_tool"),
        Index("idx_agent_tool_configs_agent", "agent_type_id"),
        Index("idx_agent_tool_configs_enabled", "enabled_for_agent"),
    )

    def __repr__(self) -> str:
        return f"<AgentToolConfig(agent={self.agent_type_id}, tool={self.tool_id})>"


class ToolUsageAudit(Base):
    """Audit log for tool usage."""

    __tablename__ = "tool_usage_audit"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Session Context
    session_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    agent_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agent_types.id"), nullable=True
    )
    tool_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tools.id"), nullable=True
    )

    # Usage Details
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Outcome
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_audit_session", "session_id"),
        Index("idx_audit_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ToolUsageAudit(id={self.id}, session={self.session_id}, status='{self.status}')>"
```

**Step 7: Update __init__.py to export models**

Modify: `backend/app/models/__init__.py`

Add these imports:

```python
from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig, ToolUsageAudit

__all__ = [
    # ... existing exports
    "Tool",
    "AgentType",
    "AgentToolConfig",
    "ToolUsageAudit",
]
```

**Step 8: Run tests to verify they pass**

```bash
poetry run pytest backend/tests/models/ -v
```

Expected: PASS - All model tests pass

**Step 9: Commit**

```bash
git add backend/app/models/tool.py backend/app/models/agent.py backend/app/models/__init__.py backend/tests/models/
git commit -m "feat: add SQLAlchemy models for dynamic tools system

- Add Tool model with JSONB definition field
- Add AgentType model with personalization fields
- Add AgentToolConfig junction model
- Add ToolUsageAudit model for tracking
- Add comprehensive model tests"
```

---

## Phase 2: Services Layer

### Task 3: Create ToolsService

**Files:**
- Create: `backend/app/services/tools_service.py`
- Create: `backend/tests/services/test_tools_service.py`

**Step 1: Write test for ToolsService**

Create: `backend/tests/services/test_tools_service.py`

```python
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
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/services/test_tools_service.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.tools_service'"

**Step 3: Implement ToolsService**

Create: `backend/app/services/tools_service.py`

```python
"""Service for managing tools and agent-tool configurations."""
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig, ToolUsageAudit

logger = logging.getLogger(__name__)


class ToolsService:
    """Service for managing tools and their assignments to agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tools_for_agent(
        self,
        agent_type_id: int,
        enabled_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get all tools assigned to an agent type.

        Args:
            agent_type_id: Agent type ID
            enabled_only: Only return enabled tools

        Returns:
            List of tool definitions ready for Claude SDK
        """
        query = (
            select(Tool)
            .join(AgentToolConfig)
            .where(AgentToolConfig.agent_type_id == agent_type_id)
        )

        if enabled_only:
            query = query.where(
                Tool.enabled == True,
                AgentToolConfig.enabled_for_agent == True
            )

        query = query.order_by(AgentToolConfig.order_index)

        result = await self.db.execute(query)
        tools = result.scalars().all()

        # Convert to SDK format
        return [self._tool_to_sdk_format(tool) for tool in tools]

    def _tool_to_sdk_format(self, tool: Tool) -> dict[str, Any]:
        """Convert Tool model to Claude SDK tool format."""
        return {
            "name": tool.name,
            "description": tool.description,
            **tool.definition  # Spread the definition (includes input_schema, etc.)
        }

    async def register_tool(self, tool_data: dict[str, Any]) -> Tool:
        """Register a new tool.

        Args:
            tool_data: Tool definition dictionary

        Returns:
            Created Tool instance
        """
        tool = Tool(**tool_data)
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)

        logger.info(f"Registered tool: {tool.name}")
        return tool

    async def get_tool_by_name(self, name: str) -> Tool | None:
        """Get tool by name."""
        result = await self.db.execute(
            select(Tool).where(Tool.name == name)
        )
        return result.scalar_one_or_none()

    async def assign_tool_to_agent(
        self,
        agent_type_id: int,
        tool_id: int,
        config: dict[str, Any] | None = None
    ) -> AgentToolConfig:
        """Assign a tool to an agent type.

        Args:
            agent_type_id: Agent type ID
            tool_id: Tool ID
            config: Optional configuration overrides

        Returns:
            Created AgentToolConfig instance
        """
        config_data = {
            "agent_type_id": agent_type_id,
            "tool_id": tool_id,
            **(config or {})
        }

        agent_tool_config = AgentToolConfig(**config_data)
        self.db.add(agent_tool_config)
        await self.db.commit()
        await self.db.refresh(agent_tool_config)

        logger.info(f"Assigned tool {tool_id} to agent {agent_type_id}")
        return agent_tool_config

    async def check_tool_allowed(
        self,
        agent_type_id: int,
        tool_name: str,
        parameters: dict | None = None
    ) -> bool:
        """Check if a tool is allowed for an agent.

        Args:
            agent_type_id: Agent type ID
            tool_name: Tool name
            parameters: Optional parameters to validate

        Returns:
            True if tool is allowed, False otherwise
        """
        result = await self.db.execute(
            select(AgentToolConfig)
            .join(Tool)
            .where(
                AgentToolConfig.agent_type_id == agent_type_id,
                Tool.name == tool_name,
                AgentToolConfig.enabled_for_agent == True,
                AgentToolConfig.allow_use == True
            )
        )

        config = result.scalar_one_or_none()

        if not config:
            return False

        # TODO: Add parameter validation against allowed/denied parameters

        return True

    async def audit_tool_usage(
        self,
        session_id: str,
        agent_type_id: int,
        tool_name: str,
        parameters: dict,
        result: dict,
        status: str,
        execution_time_ms: int,
        error_message: str | None = None
    ) -> ToolUsageAudit:
        """Log tool usage for audit trail.

        Args:
            session_id: Session ID
            agent_type_id: Agent type ID
            tool_name: Tool name
            parameters: Tool input parameters
            result: Tool output result
            status: Execution status (success/failed/denied)
            execution_time_ms: Execution time in milliseconds
            error_message: Optional error message

        Returns:
            Created ToolUsageAudit instance
        """
        # Get tool_id
        tool = await self.get_tool_by_name(tool_name)

        audit = ToolUsageAudit(
            session_id=session_id,
            agent_type_id=agent_type_id,
            tool_id=tool.id if tool else None,
            parameters=parameters,
            result=result,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
        )

        self.db.add(audit)
        await self.db.commit()

        return audit
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest backend/tests/services/test_tools_service.py -v
```

Expected: PASS - All ToolsService tests pass

**Step 5: Commit**

```bash
git add backend/app/services/tools_service.py backend/tests/services/test_tools_service.py
git commit -m "feat: add ToolsService for tool management

- Implement get_tools_for_agent with filtering
- Add register_tool for creating new tools
- Add assign_tool_to_agent for configuration
- Add check_tool_allowed for security checks
- Add audit_tool_usage for tracking
- Add comprehensive service tests"
```

---

### Task 4: Create AgentFactory

**Files:**
- Create: `backend/app/services/agent_factory.py`
- Create: `backend/tests/services/test_agent_factory.py`

**Step 1: Write test for AgentFactory**

Create: `backend/tests/services/test_agent_factory.py`

```python
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
    assert client.options.temperature == 0.8
    assert client.options.max_tokens == 150000
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
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/services/test_agent_factory.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.services.agent_factory'"

**Step 3: Implement AgentFactory**

Create: `backend/app/services/agent_factory.py`

```python
"""Factory for creating Agent SDK clients with dynamic tools."""
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from claude_agent_sdk import ClaudeSDKClient
from claude_agent_sdk.types import ClaudeAgentOptions

from app.models.agent import AgentType
from app.services.tools_service import ToolsService

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating Agent SDK clients with dynamic tool configuration."""

    def __init__(self, db: AsyncSession, tools_service: ToolsService):
        self.db = db
        self.tools_service = tools_service

    async def create_agent_client(
        self,
        agent_type_name: str,
        api_key: str | None = None
    ) -> ClaudeSDKClient:
        """Create an SDK client for the given agent type.

        Flow:
        1. Load agent type configuration from database
        2. Load tools assigned to this agent via ToolsService
        3. Initialize ClaudeSDKClient with tools
        4. Return ready-to-use client

        Args:
            agent_type_name: Agent type name (e.g., "brainstorm")
            api_key: Optional Anthropic API key (uses env var if not provided)

        Returns:
            Configured ClaudeSDKClient instance
        """
        # Get agent configuration
        result = await self.db.execute(
            select(AgentType).where(AgentType.name == agent_type_name)
        )
        agent_config = result.scalar_one_or_none()

        if not agent_config:
            raise ValueError(f"Agent type '{agent_type_name}' not found")

        if not agent_config.enabled:
            raise ValueError(f"Agent type '{agent_type_name}' is disabled")

        # Load tools for this agent
        tools = await self.tools_service.get_tools_for_agent(
            agent_config.id,
            enabled_only=True
        )

        logger.info(f"Creating SDK client for '{agent_type_name}' with {len(tools)} tools")

        # Build SDK options
        options = ClaudeAgentOptions(
            model=agent_config.model,
            system_prompt=agent_config.system_prompt,
            tools=tools if tools else None,  # SDK requires None if no tools
            temperature=agent_config.temperature,
            max_tokens=agent_config.max_context_tokens,
        )

        # Create and return client
        client = ClaudeSDKClient(options=options)

        return client

    async def get_agent_config(self, agent_type_name: str) -> dict[str, Any]:
        """Get agent configuration including personalization.

        Args:
            agent_type_name: Agent type name

        Returns:
            Dictionary with agent configuration
        """
        result = await self.db.execute(
            select(AgentType).where(AgentType.name == agent_type_name)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise ValueError(f"Agent type '{agent_type_name}' not found")

        return {
            "id": agent.id,
            "name": agent.name,
            "display_name": agent.display_name,
            "description": agent.description,
            "avatar_url": agent.avatar_url,
            "avatar_color": agent.avatar_color,
            "personality_traits": agent.personality_traits,
            "model": agent.model,
            "temperature": agent.temperature,
        }

    async def list_available_agents(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """List all available agent types.

        Args:
            enabled_only: Only return enabled agents

        Returns:
            List of agent configurations
        """
        query = select(AgentType)

        if enabled_only:
            query = query.where(AgentType.enabled == True)

        result = await self.db.execute(query)
        agents = result.scalars().all()

        return [
            {
                "id": agent.id,
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "avatar_url": agent.avatar_url,
                "avatar_color": agent.avatar_color,
                "personality_traits": agent.personality_traits,
            }
            for agent in agents
        ]
```

**Step 4: Run tests to verify they pass**

```bash
poetry run pytest backend/tests/services/test_agent_factory.py -v
```

Expected: PASS - All AgentFactory tests pass

**Step 5: Commit**

```bash
git add backend/app/services/agent_factory.py backend/tests/services/test_agent_factory.py
git commit -m "feat: add AgentFactory for dynamic SDK client creation

- Implement create_agent_client with tool loading
- Add get_agent_config for frontend
- Add list_available_agents for agent selection
- Configure SDK with agent-specific tools and settings
- Add comprehensive factory tests"
```

---

## Phase 3: Data Seeding

### Task 5: Create Seed Script for Default Agents and Tools

**Files:**
- Create: `backend/scripts/seed_agents_and_tools.py`

**Step 1: Create seed script**

Create: `backend/scripts/seed_agents_and_tools.py`

```python
"""Seed script for default agents and tools."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.tool import Tool
from app.models.agent import AgentType, AgentToolConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_default_tools(db: AsyncSession) -> dict[str, Tool]:
    """Seed default tools.

    Returns:
        Dictionary mapping tool names to Tool instances
    """
    logger.info("Seeding default tools...")

    tools_data = [
        {
            "name": "create_plan",
            "description": "Create an implementation plan from a feature brief",
            "category": "planning",
            "tool_type": "custom",
            "definition": {
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "feature_name": {
                            "type": "string",
                            "description": "Name of the feature"
                        },
                        "user_problem": {
                            "type": "string",
                            "description": "Problem this feature solves"
                        },
                        "target_users": {
                            "type": "string",
                            "description": "Target user segment"
                        },
                        "core_functionality": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of core functionality items"
                        },
                        "success_metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "KPIs for measuring success"
                        },
                        "risks": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key risks and considerations"
                        }
                    },
                    "required": ["feature_name", "user_problem", "target_users"]
                }
            },
            "is_dangerous": False,
            "requires_approval": False,
        },
        {
            "name": "web_search",
            "description": "Search the web for information",
            "category": "web",
            "tool_type": "builtin",
            "definition": {
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            "is_dangerous": False,
            "requires_approval": False,
        },
    ]

    tools = {}
    for tool_data in tools_data:
        tool = Tool(**tool_data)
        db.add(tool)
        tools[tool_data["name"]] = tool

    await db.commit()

    for tool in tools.values():
        await db.refresh(tool)

    logger.info(f"Created {len(tools)} tools")
    return tools


async def seed_default_agent_types(db: AsyncSession) -> dict[str, AgentType]:
    """Seed default agent types.

    Returns:
        Dictionary mapping agent names to AgentType instances
    """
    logger.info("Seeding default agent types...")

    # Import the actual system prompt from brainstorming service
    from app.services.brainstorming_service import BrainstormingService

    agents_data = [
        {
            "name": "brainstorm",
            "display_name": "Claude the Brainstormer",
            "description": "Creative facilitator for product discovery sessions",
            "avatar_url": "🎨",
            "avatar_color": "#f59e0b",
            "personality_traits": ["creative", "strategic", "goal-oriented"],
            "model": "claude-sonnet-4-5",
            "system_prompt": BrainstormingService.SYSTEM_PROMPT,
            "temperature": 0.8,
            "streaming_enabled": True,
            "max_context_tokens": 200000,
            "enabled": True,
            "is_default": True,
        },
    ]

    agents = {}
    for agent_data in agents_data:
        agent = AgentType(**agent_data)
        db.add(agent)
        agents[agent_data["name"]] = agent

    await db.commit()

    for agent in agents.values():
        await db.refresh(agent)

    logger.info(f"Created {len(agents)} agent types")
    return agents


async def assign_tools_to_agents(
    db: AsyncSession,
    agents: dict[str, AgentType],
    tools: dict[str, Tool]
) -> None:
    """Assign tools to agents."""
    logger.info("Assigning tools to agents...")

    assignments = [
        # Brainstorm agent gets create_plan and web_search
        {
            "agent": agents["brainstorm"],
            "tool": tools["create_plan"],
            "order_index": 1,
        },
        {
            "agent": agents["brainstorm"],
            "tool": tools["web_search"],
            "order_index": 2,
        },
    ]

    for assignment in assignments:
        config = AgentToolConfig(
            agent_type_id=assignment["agent"].id,
            tool_id=assignment["tool"].id,
            enabled_for_agent=True,
            order_index=assignment["order_index"],
            allow_use=True,
        )
        db.add(config)

    await db.commit()
    logger.info(f"Created {len(assignments)} tool assignments")


async def main():
    """Main seeding function."""
    logger.info("Starting database seeding...")

    async with async_session_maker() as db:
        # Seed tools
        tools = await seed_default_tools(db)

        # Seed agents
        agents = await seed_default_agent_types(db)

        # Assign tools to agents
        await assign_tools_to_agents(db, agents, tools)

    logger.info("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Run seed script**

```bash
cd backend
poetry run python scripts/seed_agents_and_tools.py
```

Expected: SUCCESS - Tools and agents seeded

**Step 3: Verify data exists**

```bash
docker exec -it postgres-dev psql -U postgres -d product_analysis -c "SELECT name, display_name FROM agent_types;"
docker exec -it postgres-dev psql -U postgres -d product_analysis -c "SELECT name, category FROM tools;"
```

Expected: See brainstorm agent and tools

**Step 4: Commit**

```bash
git add backend/scripts/seed_agents_and_tools.py
git commit -m "feat: add seed script for default agents and tools

- Seed create_plan and web_search tools
- Seed brainstorm agent with personalization
- Assign tools to brainstorm agent
- Use actual SYSTEM_PROMPT from BrainstormingService"
```

---

## Phase 4: API Endpoints

### Task 6: Create API Endpoints for Agents

**Files:**
- Create: `backend/app/api/agents.py`
- Create: `backend/tests/api/test_agents.py`

**Step 1: Write test for agent endpoints**

Create: `backend/tests/api/test_agents.py`

```python
"""Tests for agent API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient, db_session):
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
    response = await client.get("/api/v1/agents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_agent"
    assert data[0]["display_name"] == "Test Agent"
    assert data[0]["avatar_url"] == "🤖"


@pytest.mark.asyncio
async def test_get_agent_config(client: AsyncClient, db_session):
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

    response = await client.get("/api/v1/agents/brainstorm")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "brainstorm"
    assert data["display_name"] == "Claude the Brainstormer"
    assert "creative" in data["personality_traits"]


@pytest.mark.asyncio
async def test_get_agent_tools(client: AsyncClient, db_session):
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

    response = await client.get(f"/api/v1/agents/{agent.id}/tools")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_tool"
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/api/test_agents.py -v
```

Expected: FAIL with 404 or import error

**Step 3: Implement agent endpoints**

Create: `backend/app/api/agents.py`

```python
"""Agent API endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("")
@router.get("/")
async def list_agents(
    enabled_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all available agent types.

    Args:
        enabled_only: Only return enabled agents
        db: Database session

    Returns:
        List of agent configurations
    """
    tools_service = ToolsService(db)
    factory = AgentFactory(db, tools_service)

    agents = await factory.list_available_agents(enabled_only=enabled_only)

    return agents


@router.get("/{agent_name}")
async def get_agent_config(
    agent_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get specific agent configuration.

    Args:
        agent_name: Agent type name
        db: Database session

    Returns:
        Agent configuration

    Raises:
        HTTPException: If agent not found
    """
    tools_service = ToolsService(db)
    factory = AgentFactory(db, tools_service)

    try:
        config = await factory.get_agent_config(agent_name)
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{agent_id}/tools")
async def get_agent_tools(
    agent_id: int,
    enabled_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Get tools assigned to an agent.

    Args:
        agent_id: Agent type ID
        enabled_only: Only return enabled tools
        db: Database session

    Returns:
        List of tools in SDK format
    """
    tools_service = ToolsService(db)

    tools = await tools_service.get_tools_for_agent(
        agent_id,
        enabled_only=enabled_only
    )

    return tools
```

**Step 4: Register router in main.py**

Modify: `backend/app/main.py`

Add import and include router:

```python
from app.api import agents

# ... existing code ...

app.include_router(agents.router)
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest backend/tests/api/test_agents.py -v
```

Expected: PASS - All agent API tests pass

**Step 6: Test endpoints manually**

```bash
# Start backend if not running
poetry run uvicorn app.main:app --reload

# In another terminal
curl http://localhost:8891/api/v1/agents
curl http://localhost:8891/api/v1/agents/brainstorm
```

Expected: JSON responses with agent data

**Step 7: Commit**

```bash
git add backend/app/api/agents.py backend/app/main.py backend/tests/api/test_agents.py
git commit -m "feat: add API endpoints for agent management

- Add GET /api/v1/agents to list available agents
- Add GET /api/v1/agents/{name} to get agent config
- Add GET /api/v1/agents/{id}/tools to list agent tools
- Add comprehensive API tests"
```

---

## Phase 5: Update BrainstormingService

### Task 7: Integrate Dynamic Tools into BrainstormingService

**Files:**
- Modify: `backend/app/services/brainstorming_service.py`
- Modify: `backend/app/api/brainstorms.py`

**Step 1: Write test for tool integration**

Create: `backend/tests/services/test_brainstorming_dynamic_tools.py`

```python
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
    assert service.client.options.temperature == 0.9
    assert len(service.client.options.tools) == 1
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest backend/tests/services/test_brainstorming_dynamic_tools.py -v
```

Expected: FAIL - Service doesn't support agent_factory yet

**Step 3: Update BrainstormingService to use AgentFactory**

Modify: `backend/app/services/brainstorming_service.py`

Replace the `__init__` and `_ensure_connected` methods:

```python
class BrainstormingService:
    """Service for brainstorming with Claude via streaming using Agent SDK."""

    SYSTEM_PROMPT = """..."""  # Keep existing prompt

    def __init__(
        self,
        api_key: str,
        agent_factory: "AgentFactory" = None,
        agent_name: str = "brainstorm",
        model: str = "claude-sonnet-4-5"
    ) -> None:
        """Initialize the brainstorming service.

        Args:
            api_key: Anthropic API key
            agent_factory: Optional AgentFactory for dynamic tool loading
            agent_name: Agent type name to use (default: "brainstorm")
            model: Claude model to use (fallback if no agent_factory)
        """
        logger.warning("[SERVICE] __init__ called")
        self.api_key = api_key
        self.agent_factory = agent_factory
        self.agent_name = agent_name
        self.model = model
        self.client = None
        self.connected = False

        # Set API key in environment for Claude SDK
        os.environ['ANTHROPIC_API_KEY'] = api_key
        logger.warning("[SERVICE] API key set in environment")

    async def _ensure_connected(self):
        """Ensure client is connected."""
        logger.warning("[SERVICE] _ensure_connected called")
        if not self.connected:
            logger.warning("[SERVICE] Not connected, initializing client...")

            if self.agent_factory:
                # Use agent factory to create client with dynamic tools
                logger.warning(f"[SERVICE] Creating client via AgentFactory for agent '{self.agent_name}'")
                self.client = await self.agent_factory.create_agent_client(self.agent_name)
            else:
                # Fallback: Create client with static config (backwards compatibility)
                logger.warning(f"[SERVICE] Creating client with static config (no AgentFactory)")
                options = ClaudeAgentOptions(
                    model=self.model,
                    system_prompt=self.SYSTEM_PROMPT,
                )
                self.client = ClaudeSDKClient(options=options)

            logger.warning("[SERVICE] Calling client.connect()...")
            await self.client.connect()
            logger.warning("[SERVICE] client.connect() completed")
            self.connected = True
            logger.warning("[SERVICE] Connected flag set to True")
```

**Step 4: Update brainstorms.py to pass AgentFactory**

Modify: `backend/app/api/brainstorms.py`

Update the websocket endpoint to initialize service with factory:

```python
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService

# ... existing code ...

@router.websocket("/ws/{session_id}")
async def websocket_brainstorm(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for interactive brainstorming."""
    await websocket.accept()
    logger.info(f"[WS] Client connected to session {session_id}")

    # Independent database session
    async with async_session_maker() as db:
        try:
            # ... existing session verification code ...

            # Initialize services for dynamic tools
            tools_service = ToolsService(db)
            agent_factory = AgentFactory(db, tools_service)

            # Main message loop
            while True:
                data = await websocket.receive_json()
                logger.info(f"[WS] Received: {data['type']}")

                if data["type"] == "user_message":
                    await handle_user_message(
                        websocket, db, session_id, data["content"],
                        agent_factory  # Pass factory
                    )

                elif data["type"] == "interaction":
                    # ... existing interaction handling ...
                    await handle_interaction(
                        websocket, db, session_id,
                        block_id, value,
                        agent_factory  # Pass factory
                    )

        except WebSocketDisconnect:
            # ... existing error handling ...


async def handle_user_message(
    websocket: WebSocket,
    db,
    session_id: str,
    content: str,
    agent_factory: AgentFactory  # New parameter
):
    """Handle user text message."""
    # ... existing message saving code ...

    # Stream Claude response with dynamic tools
    await stream_claude_response(websocket, db, session_id, agent_factory)


async def handle_interaction(
    websocket: WebSocket,
    db,
    session_id: str,
    block_id: str,
    value: str | list[str],
    agent_factory: AgentFactory  # New parameter
):
    """Handle user interaction with button/select."""
    # ... existing interaction saving code ...

    # Stream Claude response with dynamic tools
    await stream_claude_response(websocket, db, session_id, agent_factory)


async def stream_claude_response(
    websocket: WebSocket,
    db,
    session_id: str,
    agent_factory: AgentFactory  # New parameter
):
    """Stream Claude's response block-by-block."""
    # ... existing conversation history building ...

    message_id = str(uuid4())
    collected_blocks = []

    # Create service with agent factory
    async with BrainstormingService(
        api_key=settings.anthropic_api_key,
        agent_factory=agent_factory,
        agent_name="brainstorm"  # Use brainstorm agent
    ) as service:
        # ... existing streaming code ...
```

**Step 5: Run tests to verify they pass**

```bash
poetry run pytest backend/tests/services/test_brainstorming_dynamic_tools.py -v
```

Expected: PASS - Service uses dynamic tools

**Step 6: Test end-to-end**

```bash
# Restart backend
poetry run uvicorn app.main:app --reload

# Frontend: Create new brainstorm session, verify it works
```

Expected: Brainstorming works with dynamic tool loading

**Step 7: Commit**

```bash
git add backend/app/services/brainstorming_service.py backend/app/api/brainstorms.py backend/tests/services/test_brainstorming_dynamic_tools.py
git commit -m "feat: integrate dynamic tools into BrainstormingService

- Add agent_factory parameter to service __init__
- Use AgentFactory to create SDK client with dynamic tools
- Update WebSocket handlers to pass factory
- Maintain backwards compatibility with static config
- Add integration tests"
```

---

## Phase 6: Frontend Integration

### Task 8: Add Agent Config API to Frontend

**Files:**
- Create: `frontend/src/api/agents.ts`
- Create: `frontend/src/types/agent.ts`

**Step 1: Create TypeScript types for agents**

Create: `frontend/src/types/agent.ts`

```typescript
/**
 * Agent type definition with personalization.
 */
export interface AgentType {
  id: number
  name: string
  display_name: string
  description?: string
  avatar_url?: string
  avatar_color: string
  personality_traits: string[]
  model: string
  temperature: number
}

/**
 * Tool definition.
 */
export interface Tool {
  name: string
  description: string
  category: string
}
```

**Step 2: Create API client for agents**

Create: `frontend/src/api/agents.ts`

```typescript
/**
 * API client for agent management.
 */
import { apiClient } from './client'
import type { AgentType, Tool } from '@/types/agent'

/**
 * List all available agents.
 */
export async function listAgents(enabledOnly: boolean = true): Promise<AgentType[]> {
  const response = await apiClient.get<AgentType[]>('/agents', {
    params: { enabled_only: enabledOnly }
  })
  return response.data
}

/**
 * Get specific agent configuration.
 */
export async function getAgentConfig(agentName: string): Promise<AgentType> {
  const response = await apiClient.get<AgentType>(`/agents/${agentName}`)
  return response.data
}

/**
 * Get tools assigned to an agent.
 */
export async function getAgentTools(agentId: number, enabledOnly: boolean = true): Promise<Tool[]> {
  const response = await apiClient.get<Tool[]>(`/agents/${agentId}/tools`, {
    params: { enabled_only: enabledOnly }
  })
  return response.data
}
```

**Step 3: Update Pinia store to load agent config**

Modify: `frontend/src/stores/brainstorm.ts`

Add agent state and loading:

```typescript
import { getAgentConfig } from '@/api/agents'
import type { AgentType } from '@/types/agent'

// ... existing imports ...

export const useBrainstormStore = defineStore('brainstorm', () => {
  // ... existing state ...

  const currentAgentConfig = ref<AgentType | null>(null)
  const agentConfigLoading = ref(false)

  // ... existing functions ...

  async function fetchAgentConfig(agentName: string) {
    agentConfigLoading.value = true
    try {
      currentAgentConfig.value = await getAgentConfig(agentName)
    } catch (error) {
      console.error('[STORE] Failed to fetch agent config:', error)
      // Use default fallback
      currentAgentConfig.value = {
        id: 0,
        name: agentName,
        display_name: 'Claude',
        avatar_url: '🤖',
        avatar_color: '#6366f1',
        personality_traits: [],
        model: 'claude-sonnet-4-5',
        temperature: 0.7,
      }
    } finally {
      agentConfigLoading.value = false
    }
  }

  return {
    // ... existing exports ...
    currentAgentConfig,
    agentConfigLoading,
    fetchAgentConfig,
  }
})
```

**Step 4: Commit**

```bash
git add frontend/src/api/agents.ts frontend/src/types/agent.ts frontend/src/stores/brainstorm.ts
git commit -m "feat: add agent API client and store integration

- Add AgentType and Tool TypeScript types
- Add agents API client with list/get methods
- Add agent config state to brainstorm store
- Add fetchAgentConfig action with fallback"
```

---

### Task 9: Display Agent Personalization in BrainstormChat

**Files:**
- Modify: `frontend/src/components/BrainstormChat.vue`

**Step 1: Load agent config when session loads**

Modify: `frontend/src/components/BrainstormChat.vue`

Update script section:

```typescript
// ... existing imports ...
import { computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

// ... existing code ...

const currentAgentConfig = computed(() => store.currentAgentConfig)

// ... existing onMounted ...
onMounted(async () => {
  await store.fetchSession(props.sessionId)

  // Load agent config (default to brainstorm)
  await store.fetchAgentConfig('brainstorm')

  connectWebSocket()
  scrollToBottom()
})
```

**Step 2: Update avatar display to use agent config**

Modify template section in `frontend/src/components/BrainstormChat.vue`

Replace the Bot avatar sections:

```vue
<!-- For regular messages -->
<Avatar class="h-6 w-6">
  <AvatarFallback
    :class="message.role === 'assistant' ? '' : ''"
    :style="message.role === 'assistant' && currentAgentConfig
      ? { backgroundColor: currentAgentConfig.avatar_color }
      : {}"
  >
    <!-- Agent avatar -->
    <template v-if="message.role === 'assistant' && currentAgentConfig">
      <span v-if="isEmoji(currentAgentConfig.avatar_url || '')">
        {{ currentAgentConfig.avatar_url }}
      </span>
      <img
        v-else-if="currentAgentConfig.avatar_url"
        :src="currentAgentConfig.avatar_url"
        alt="avatar"
        class="w-full h-full object-cover"
      />
      <Bot v-else class="h-5 w-5" />
    </template>
    <!-- User avatar -->
    <User v-if="message.role === 'user'" class="h-5 w-5" />
  </AvatarFallback>
</Avatar>
<span class="text-xs font-semibold">
  {{ message.role === 'user' ? 'You' : (currentAgentConfig?.display_name || 'Claude') }}
</span>
```

**Step 3: Add helper function for emoji detection**

Add to script section:

```typescript
function isEmoji(str: string): boolean {
  return /\p{Emoji}/u.test(str)
}
```

**Step 4: Update streaming message avatar similarly**

Find the streaming message section and update it:

```vue
<!-- Streaming Message or Waiting for Response -->
<div v-if="store.streamingMessageId || waitingForResponse" class="flex justify-start">
  <div class="max-w-[80%] rounded-lg p-4 bg-muted">
    <div class="flex items-center gap-2 mb-2">
      <Avatar class="h-6 w-6">
        <AvatarFallback
          :style="currentAgentConfig
            ? { backgroundColor: currentAgentConfig.avatar_color }
            : { backgroundColor: '#6366f1' }"
        >
          <span v-if="currentAgentConfig && isEmoji(currentAgentConfig.avatar_url || '')">
            {{ currentAgentConfig.avatar_url }}
          </span>
          <img
            v-else-if="currentAgentConfig?.avatar_url"
            :src="currentAgentConfig.avatar_url"
            alt="avatar"
            class="w-full h-full object-cover"
          />
          <Bot v-else class="h-5 w-5" />
        </AvatarFallback>
      </Avatar>
      <span class="text-xs font-semibold">
        {{ currentAgentConfig?.display_name || 'Claude' }}
      </span>
    </div>
    <!-- ... rest of streaming content ... -->
  </div>
</div>
```

**Step 5: Test in browser**

```bash
# Frontend should be running
npm run dev

# Visit http://localhost:8892/brainstorm/{session_id}
```

Expected: See "Claude the Brainstormer" with 🎨 emoji and orange background

**Step 6: Commit**

```bash
git add frontend/src/components/BrainstormChat.vue
git commit -m "feat: display agent personalization in chat

- Load agent config when session starts
- Display custom avatar (emoji or image) with color
- Show agent display_name instead of generic 'Claude'
- Add emoji detection helper function
- Update both regular and streaming message avatars"
```

---

### Task 10: Create Agent Selector Component

**Files:**
- Create: `frontend/src/components/AgentSelector.vue`
- Modify: `frontend/src/views/BrainstormListView.vue`

**Step 1: Create AgentSelector component**

Create: `frontend/src/components/AgentSelector.vue`

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Bot } from 'lucide-vue-next'
import { listAgents } from '@/api/agents'
import type { AgentType } from '@/types/agent'

const emit = defineEmits<{
  select: [agent: AgentType]
}>()

const agents = ref<AgentType[]>([])
const loading = ref(false)
const selectedAgent = ref<string | null>(null)

async function loadAgents() {
  loading.value = true
  try {
    agents.value = await listAgents()

    // Auto-select default agent
    const defaultAgent = agents.value.find(a => a.name === 'brainstorm')
    if (defaultAgent) {
      selectedAgent.value = defaultAgent.name
    }
  } catch (error) {
    console.error('[AGENT_SELECTOR] Failed to load agents:', error)
  } finally {
    loading.value = false
  }
}

function selectAgent(agent: AgentType) {
  selectedAgent.value = agent.name
  emit('select', agent)
}

function isEmoji(str: string): boolean {
  return /\p{Emoji}/u.test(str)
}

onMounted(() => {
  loadAgents()
})
</script>

<template>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold">Choose Your AI Assistant</h3>

    <div v-if="loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading agents...</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="agent in agents"
        :key="agent.id"
        @click="selectAgent(agent)"
        :class="[
          'cursor-pointer transition-all hover:shadow-md',
          selectedAgent === agent.name ? 'border-primary ring-2 ring-primary' : ''
        ]"
      >
        <CardHeader>
          <div class="flex items-center gap-3">
            <Avatar class="h-12 w-12">
              <AvatarFallback :style="{ backgroundColor: agent.avatar_color }">
                <span v-if="agent.avatar_url && isEmoji(agent.avatar_url)" class="text-2xl">
                  {{ agent.avatar_url }}
                </span>
                <img
                  v-else-if="agent.avatar_url"
                  :src="agent.avatar_url"
                  alt="avatar"
                  class="w-full h-full object-cover"
                />
                <Bot v-else class="h-6 w-6" />
              </AvatarFallback>
            </Avatar>
            <div class="flex-1 min-w-0">
              <h4 class="font-semibold truncate">{{ agent.display_name }}</h4>
              <p v-if="agent.description" class="text-xs text-muted-foreground line-clamp-2">
                {{ agent.description }}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent v-if="agent.personality_traits.length > 0">
          <div class="flex flex-wrap gap-1">
            <Badge
              v-for="trait in agent.personality_traits"
              :key="trait"
              variant="secondary"
              class="text-xs"
            >
              {{ trait }}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
```

**Step 2: Update BrainstormListView to show selector**

Modify: `frontend/src/views/BrainstormListView.vue`

Add import and component:

```vue
<script setup lang="ts">
// ... existing imports ...
import AgentSelector from '@/components/AgentSelector.vue'
import type { AgentType } from '@/types/agent'

// ... existing code ...

const showAgentSelector = ref(false)
const selectedAgent = ref<AgentType | null>(null)

async function handleCreate() {
  showAgentSelector.value = true
}

async function handleAgentSelected(agent: AgentType) {
  selectedAgent.value = agent

  try {
    // Create session without title/description - they will be inferred later
    const session = await store.createSession({})

    // TODO: Store selected agent with session (future enhancement)

    router.push(`/brainstorm/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
  } finally {
    showAgentSelector.value = false
  }
}

function cancelAgentSelection() {
  showAgentSelector.value = false
  selectedAgent.value = null
}
</script>

<template>
  <div class="container py-8 space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold">Brainstorming Sessions</h1>
        <p class="text-muted-foreground">Create and manage your product discovery sessions</p>
      </div>
      <Button @click="handleCreate">
        <Plus class="mr-2 h-4 w-4" />
        New Session
      </Button>
    </div>

    <!-- Agent Selector Dialog -->
    <Card v-if="showAgentSelector" class="p-6">
      <AgentSelector @select="handleAgentSelected" />
      <div class="flex justify-end mt-4">
        <Button variant="ghost" @click="cancelAgentSelection">
          Cancel
        </Button>
      </div>
    </Card>

    <!-- Existing sessions list -->
    <div v-if="!showAgentSelector">
      <!-- ... existing sessions list code ... -->
    </div>
  </div>
</template>
```

**Step 3: Test in browser**

```bash
npm run dev

# Visit http://localhost:8892/brainstorm
# Click "New Session"
```

Expected: See agent selector with "Claude the Brainstormer" card

**Step 4: Commit**

```bash
git add frontend/src/components/AgentSelector.vue frontend/src/views/BrainstormListView.vue
git commit -m "feat: add agent selector UI for session creation

- Create AgentSelector component with grid layout
- Display agent cards with avatar, name, description, traits
- Highlight selected agent with border
- Integrate selector into BrainstormListView
- Auto-select default brainstorm agent"
```

---

## Phase 7: Testing & Documentation

### Task 11: Run All Tests and Verify Quality Gates

**Files:**
- None (verification only)

**Step 1: Run backend tests**

```bash
cd backend
poetry run pytest -v --cov=app --cov-report=term-missing
```

Expected: All tests pass with 90%+ coverage

**Step 2: Run backend linting**

```bash
poetry run ruff check .
poetry run mypy app
```

Expected: No errors

**Step 3: Run frontend tests**

```bash
cd ../frontend
npm run test:run
```

Expected: All tests pass

**Step 4: Run frontend linting**

```bash
npm run lint
```

Expected: No errors

**Step 5: Manual E2E test**

1. Start backend: `cd backend && poetry run uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Visit `http://localhost:8892/brainstorm`
4. Click "New Session"
5. Select agent (should see Claude the Brainstormer)
6. Create session
7. Verify chat shows personalized avatar and name
8. Send message and verify response

Expected: Full flow works end-to-end

**Step 6: Commit**

```bash
git add .
git commit -m "test: verify all quality gates pass

- Backend tests: 90%+ coverage
- Frontend tests: all pass
- No linting errors
- Manual E2E test successful"
```

---

## Phase 8: Documentation

### Task 12: Update Project Documentation

**Files:**
- Modify: `CLAUDE.md`
- Create: `docs/guides/dynamic-tools-usage.md`

**Step 1: Update CLAUDE.md with new features**

Modify: `CLAUDE.md`

Add section after "Architecture":

```markdown
## Dynamic Tools System

The application supports a flexible, database-driven system for managing Claude Agent SDK tools and personalized agents.

### Agent Types

Each agent type has:
- **Identity**: name, display_name, description
- **Personalization**: avatar (emoji/URL), color, personality traits
- **Configuration**: model, system_prompt, temperature
- **Tools**: Dynamic assignment of available tools

Current agents:
- **brainstorm** (Claude the Brainstormer 🎨): Creative facilitator for product discovery

### Tools

Tools are Claude Agent SDK functions that can be called during conversations. They are stored in the database and dynamically loaded per agent type.

Current tools:
- **create_plan**: Creates implementation plan from feature brief
- **web_search**: Searches web for information

### Adding New Agents

1. Create agent type in database (via seed script or API)
2. Assign tools to agent
3. Agent automatically available in UI

### Adding New Tools

1. Register tool in database with definition
2. Assign to agent types
3. Tool automatically available when agent is used

See `docs/design/dynamic-tools-system.md` for full architecture.
See `docs/guides/dynamic-tools-usage.md` for usage examples.
```

**Step 2: Create usage guide**

Create: `docs/guides/dynamic-tools-usage.md`

```markdown
# Dynamic Tools System - Usage Guide

## Overview

The Dynamic Tools System allows you to manage Claude Agent SDK tools and personalized agents through the database, without code changes.

## Creating a New Agent Type

### Via Python Script

```python
from app.models.agent import AgentType
from app.database import async_session_maker

async def create_custom_agent():
    async with async_session_maker() as db:
        agent = AgentType(
            name="code_reviewer",
            display_name="Rita the Reviewer",
            description="Code review expert with focus on best practices",
            avatar_url="👩‍💻",
            avatar_color="#3b82f6",
            personality_traits=["analytical", "thorough", "constructive"],
            model="claude-opus-4-5",
            system_prompt="You are an expert code reviewer...",
            temperature=0.3,
        )
        db.add(agent)
        await db.commit()
```

### Via API (Future)

```bash
curl -X POST http://localhost:8891/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code_reviewer",
    "display_name": "Rita the Reviewer",
    "avatar_url": "👩‍💻",
    "avatar_color": "#3b82f6",
    "model": "claude-opus-4-5",
    "system_prompt": "You are an expert code reviewer..."
  }'
```

## Registering a New Tool

### Via Python Script

```python
from app.services.tools_service import ToolsService

tool_def = {
    "name": "search_codebase",
    "description": "Search for code patterns in the codebase",
    "category": "code",
    "tool_type": "custom",
    "definition": {
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern to search (e.g., '*.py')"
                }
            },
            "required": ["query"]
        }
    },
    "is_dangerous": False,
}

async with async_session_maker() as db:
    tools_service = ToolsService(db)
    tool = await tools_service.register_tool(tool_def)
```

## Assigning Tools to Agents

```python
from app.services.tools_service import ToolsService

async with async_session_maker() as db:
    tools_service = ToolsService(db)

    # Get agent and tool
    agent = await db.execute(select(AgentType).where(AgentType.name == "code_reviewer"))
    tool = await tools_service.get_tool_by_name("search_codebase")

    # Assign with optional config
    await tools_service.assign_tool_to_agent(
        agent_type_id=agent.id,
        tool_id=tool.id,
        config={
            "enabled_for_agent": True,
            "order_index": 1,
            "usage_limit": 50,  # Max 50 uses per session
        }
    )
```

## Using Agents in Code

```python
from app.services.agent_factory import AgentFactory
from app.services.tools_service import ToolsService

async with async_session_maker() as db:
    tools_service = ToolsService(db)
    agent_factory = AgentFactory(db, tools_service)

    # Create SDK client with all configured tools
    client = await agent_factory.create_agent_client("code_reviewer")

    # Use client for conversation
    await client.query("Review this code...")
```

## Security Considerations

- Tools marked `is_dangerous=True` should require approval
- Use `allowed_parameters` to restrict tool inputs
- All tool usage is logged in `tool_usage_audit` table
- Review audit logs regularly for suspicious activity

## Best Practices

1. **Tool Naming**: Use snake_case, descriptive names
2. **Descriptions**: Write clear descriptions for Claude to understand when to use
3. **Input Schemas**: Provide detailed schemas with descriptions
4. **Agent Personalities**: Choose temperature based on use case:
   - Creative tasks (brainstorming): 0.7-0.9
   - Analytical tasks (code review): 0.3-0.5
   - Balanced: 0.5-0.7
5. **Testing**: Always test new tools with sample inputs before production use

## Troubleshooting

### Tool Not Available to Agent

1. Check tool is enabled: `SELECT * FROM tools WHERE name='tool_name'`
2. Check assignment exists: `SELECT * FROM agent_tool_configs WHERE agent_type_id=X AND tool_id=Y`
3. Check `enabled_for_agent=true` and `allow_use=true`

### Agent Not Showing in UI

1. Check agent is enabled: `SELECT * FROM agent_types WHERE name='agent_name'`
2. Check frontend fetched agents: Console should show API call
3. Clear browser cache and reload

### Tool Usage Not Working

1. Check audit logs: `SELECT * FROM tool_usage_audit ORDER BY created_at DESC LIMIT 10`
2. Check for errors in `error_message` field
3. Verify tool definition schema matches SDK expectations
```

**Step 3: Commit**

```bash
git add CLAUDE.md docs/guides/dynamic-tools-usage.md
git commit -m "docs: document dynamic tools system

- Add overview to CLAUDE.md
- Create comprehensive usage guide
- Include examples for creating agents and tools
- Document security considerations and best practices
- Add troubleshooting section"
```

---

## Execution Complete

**Summary:**

You have successfully implemented a complete Dynamic Tools System with:

✅ **Database**: 4 tables (tools, agent_types, agent_tool_configs, tool_usage_audit)
✅ **Models**: SQLAlchemy models with JSONB fields for flexibility
✅ **Services**: ToolsService and AgentFactory for dynamic loading
✅ **API**: Endpoints for listing agents and tools
✅ **Integration**: BrainstormingService uses dynamic tools
✅ **Frontend**: Agent personalization display and selection UI
✅ **Seeding**: Default brainstorm agent with tools
✅ **Tests**: Comprehensive test coverage (90%+)
✅ **Documentation**: Usage guides and examples

**Next Steps (Optional Enhancements):**

1. **Tool Execution**: Implement actual tool handler functions (create_plan, web_search)
2. **Admin UI**: Build frontend for managing tools and agents
3. **Tool Categories**: Filter tools by category in UI
4. **Usage Analytics**: Dashboard showing tool usage statistics
5. **Tool Marketplace**: Share and import tools from community

---

**Plan complete and saved to `docs/plans/2026-01-09-dynamic-tools-system.md`.**

Two execution options:

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)**
- Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
