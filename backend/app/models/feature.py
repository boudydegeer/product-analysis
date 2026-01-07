"""Feature model for tracking feature requests."""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
import enum

from sqlalchemy import String, Text, Integer, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class FeatureStatus(str, enum.Enum):
    """Feature request status."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Feature(Base, TimestampMixin):
    """Feature request model."""

    __tablename__ = "features"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeatureStatus] = mapped_column(
        SQLEnum(FeatureStatus),
        default=FeatureStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    github_issue_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    analysis_workflow_run_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Webhook tracking
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    webhook_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Polling tracking
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis",
        back_populates="feature",
        cascade="all, delete-orphan",
    )
