"""Analysis model for storing feature analysis results."""

from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.feature import Feature


class Analysis(Base, TimestampMixin):
    """Feature analysis result model."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("features.id", ondelete="CASCADE"),
        nullable=False,
    )
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    feature: Mapped["Feature"] = relationship("Feature", back_populates="analyses")
