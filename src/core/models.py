"""
Domain layer models - business logic representation.
These models represent the core business entities independent of storage or API.
"""

from enum import Enum
from pydantic import BaseModel
from datetime import date


# --- Domain Enums ---
class SwitchStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class MeasurementType(str, Enum):
    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"
    POWER = "POWER"


class ComponentType(str, Enum):
    TRANSFORMER = "TRANSFORMER"
    LINE = "LINE"
    SWITCH = "SWITCH"


# --- Report Domain Models ---


# KPI 1
class ComponentTypeCount(BaseModel):
    component_type: str
    count: int


# KPI 2
class TransformerCapacity(BaseModel):
    voltage_kv: float
    total_capacity_mva: float


# KPI 3
class LineLength(BaseModel):
    voltage_kv: float
    total_length_km: float


# KPI 4
class DailyAverage(BaseModel):
    day: date
    measurement_type: str
    component_type: str
    avg_value: float


class ReportSummary(BaseModel):
    components_by_type: list[ComponentTypeCount]
    transformer_capacity_by_voltage: list[TransformerCapacity]
    line_length_by_voltage: list[LineLength]


class FinalReportSchema(BaseModel):
    summary: ReportSummary
    daily_averages: list[DailyAverage]
