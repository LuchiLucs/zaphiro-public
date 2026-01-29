"""
Database/Storage layer models using SQLModel.
These are the ORM models that map directly to database tables.
"""

from datetime import datetime, UTC
from core.models import ComponentType, MeasurementType, SwitchStatus
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


# Component Models
class ComponentDB(SQLModel, table=True):
    """
    Base component table using Single Table Inheritance pattern.
    All component types are stored in one table with discriminator.
    """

    __tablename__ = "components"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    substation: str = Field(index=True)

    # Discriminator field to identify component type
    component_type: ComponentType = Field(index=True)

    # Transformer-specific fields (nullable for other types)
    capacity_mva: float | None = Field(default=None)

    # Line-specific fields (nullable for other types)
    length_km: float | None = Field(default=None)

    # Common voltage field for Transformer and Line
    voltage_kv: float | None = Field(default=None)

    # Switch-specific fields (nullable for other types)
    status: SwitchStatus | None = Field(default=None)

    # Relationships
    measurements: list["MeasurementDB"] = Relationship(
        back_populates="component", cascade_delete=True
    )

    # Handle duplicates
    __table_args__ = (
        UniqueConstraint("name", "substation", name="uq_component_name_substation"),
    )


class MeasurementDB(SQLModel, table=True):
    """Measurement table storing sensor readings."""

    __tablename__ = "measurements"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True, default_factory=lambda: datetime.now(UTC))
    value: float
    measurement_type: MeasurementType = Field(index=True)

    # Foreign key to component
    component_id: int = Field(foreign_key="components.id", index=True)

    # Relationship
    component: ComponentDB = Relationship(back_populates="measurements")

    # Handle duplicates
    __table_args__ = (
        UniqueConstraint(
            "timestamp",
            "component_id",
            "measurement_type",
            name="uq_meas_time_comp_type",
        ),
    )


class ReportDB(SQLModel, table=True):
    """Report table storing generated report metadata."""

    __tablename__ = "reports"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    start_date: datetime = Field(index=True)
    end_date: datetime = Field(index=True)
    status: str = Field(default="pending")  # pending, processing, completed, failed
    result_json: str | None = Field(default=None)  # JSON string of report data
    error_message: str | None = Field(default=None)
