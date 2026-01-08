"""Idea model for product ideas management."""
from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class IdeaStatus(str, enum.Enum):
    """Idea statuses."""

    BACKLOG = "backlog"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class IdeaPriority(str, enum.Enum):
    """Idea priorities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Idea(Base, TimestampMixin):
    """Idea model for product ideas."""

    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Status and priority
    status: Mapped[IdeaStatus] = mapped_column(
        SQLEnum(IdeaStatus),
        default=IdeaStatus.BACKLOG,
        nullable=False,
    )
    priority: Mapped[IdeaPriority] = mapped_column(
        SQLEnum(IdeaPriority),
        default=IdeaPriority.MEDIUM,
        nullable=False,
    )

    # AI evaluation fields (1-10 scale)
    business_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    technical_complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional fields
    estimated_effort: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market_fit_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Constraints for 1-10 scale
    __table_args__ = (
        CheckConstraint(
            "business_value IS NULL OR (business_value >= 1 AND business_value <= 10)",
            name="check_business_value_range",
        ),
        CheckConstraint(
            "technical_complexity IS NULL OR (technical_complexity >= 1 AND technical_complexity <= 10)",
            name="check_technical_complexity_range",
        ),
    )
