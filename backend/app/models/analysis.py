"""Analysis model for storing feature analysis results."""

from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, JSON, Text, DateTime
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

    # Legacy field - keep for backward compatibility
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Flattened summary fields
    summary_overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_key_points: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    summary_metrics: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Flattened implementation fields
    implementation_architecture: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    implementation_technical_details: Mapped[
        Optional[list[dict[str, Any]]]
    ] = mapped_column(JSON, nullable=True)
    implementation_data_flow: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Flattened risk fields
    risks_technical_risks: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    risks_security_concerns: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    risks_scalability_issues: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON, nullable=True
    )
    risks_mitigation_strategies: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )

    # Flattened recommendation fields
    recommendations_improvements: Mapped[
        Optional[list[dict[str, Any]]]
    ] = mapped_column(JSON, nullable=True)
    recommendations_best_practices: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )
    recommendations_next_steps: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )

    # Metadata
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    feature: Mapped["Feature"] = relationship("Feature", back_populates="analyses")
