"""Agent models for dynamic agent management."""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tool import Tool


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
    personality_traits: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), default=list
    )

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
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
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
    allowed_parameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    denied_parameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    parameter_defaults: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    agent_type: Mapped["AgentType"] = relationship("AgentType", back_populates="tool_configs")
    tool: Mapped["Tool"] = relationship("Tool", back_populates="agent_configs")  # noqa: F821

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
    parameters: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    result: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )

    # Outcome
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_audit_session", "session_id"),
        Index("idx_audit_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ToolUsageAudit(id={self.id}, session={self.session_id}, status='{self.status}')>"
