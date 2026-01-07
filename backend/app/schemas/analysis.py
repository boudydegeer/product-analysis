"""Pydantic schemas for Analysis model."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalysisResponse(BaseModel):
    """Schema for Analysis response with all fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    feature_id: UUID
    result: dict[str, Any]
    tokens_used: int
    model_used: str
    completed_at: Optional[datetime] = None
    created_at: datetime
