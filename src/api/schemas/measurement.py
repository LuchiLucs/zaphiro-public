"""Measurement API schemas."""

from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict
from core.models import MeasurementType


class MeasurementCreate(BaseModel):
    """Schema for creating a measurement."""

    component_id: int = Field(..., gt=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    value: float
    measurement_type: MeasurementType


class MeasurementResponse(BaseModel):
    """Measurement response schema."""

    id: int
    component_id: int
    timestamp: datetime
    value: float
    measurement_type: MeasurementType

    model_config = ConfigDict(from_attributes=True)
