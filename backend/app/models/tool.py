"""Tool model for dynamic tool management."""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Integer, DateTime, Index, func
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.agent import AgentToolConfig


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
    definition: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )

    # Configuration
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_dangerous: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    tags: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), default=list
    )
    example_usage: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
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
