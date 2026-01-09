"""CodebaseExploration model for tracking codebase analysis requests."""

from typing import Optional
from datetime import datetime
import enum

from sqlalchemy import String, Text, DateTime, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CodebaseExplorationStatus(str, enum.Enum):
    """Status of a codebase exploration request."""

    PENDING = "pending"
    INVESTIGATING = "investigating"
    COMPLETED = "completed"
    FAILED = "failed"


class CodebaseExploration(Base, TimestampMixin):
    """Codebase exploration request model.

    Tracks requests for Claude to explore and analyze the codebase,
    typically triggered during brainstorming sessions to gather context
    about existing patterns, implementations, or architecture.
    """

    __tablename__ = "codebase_explorations"

    # Primary Key - exploration ID like "exp-abc123"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    # Context - which session/message triggered this exploration
    session_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Exploration request
    query: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default="full", nullable=False)
    focus: Mapped[str] = mapped_column(String(20), default="patterns", nullable=False)

    # GitHub workflow tracking
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    workflow_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[CodebaseExplorationStatus] = mapped_column(
        SQLEnum(CodebaseExplorationStatus),
        default=CodebaseExplorationStatus.PENDING,
        nullable=False,
    )

    # Results
    results: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    formatted_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Completion tracking
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_codebase_explorations_session_id", "session_id"),
        Index("idx_codebase_explorations_status", "status"),
        Index("idx_codebase_explorations_workflow_run_id", "workflow_run_id"),
    )

    def __repr__(self) -> str:
        return f"<CodebaseExploration(id='{self.id}', status='{self.status.value}', query='{self.query[:50]}...')>"
