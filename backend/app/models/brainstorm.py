"""Brainstorm session and message models."""
from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class BrainstormSessionStatus(str, enum.Enum):
    """Brainstorm session statuses."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    """Message roles."""

    USER = "user"
    ASSISTANT = "assistant"


class BrainstormSession(Base, TimestampMixin):
    """Brainstorm session model."""

    __tablename__ = "brainstorm_sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BrainstormSessionStatus] = mapped_column(
        SQLEnum(BrainstormSessionStatus),
        default=BrainstormSessionStatus.ACTIVE,
        nullable=False,
    )

    # Relationships
    messages: Mapped[list["BrainstormMessage"]] = relationship(
        "BrainstormMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BrainstormMessage(Base, TimestampMixin):
    """Brainstorm message model."""

    __tablename__ = "brainstorm_messages"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("brainstorm_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    session: Mapped["BrainstormSession"] = relationship(
        "BrainstormSession", back_populates="messages"
    )
