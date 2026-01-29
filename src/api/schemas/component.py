"""Component API schemas - request/response models."""

from typing import Literal, Annotated

from pydantic import BaseModel, Field
from core.models import ComponentType, SwitchStatus


# --- Base Schema ---
class ComponentCreateBase(BaseModel):
    """Shared fields for all components when create."""

    name: str = Field(..., min_length=1, max_length=100)
    substation: str = Field(..., min_length=1, max_length=100)


class ComponentUpdateBase(BaseModel):
    """Shared fields for all components when update."""

    name: str | None = Field(None, min_length=1, max_length=100)
    substation: str | None = None


class ComponentResponseBase(BaseModel):
    """Shared fields for all components when response."""

    id: int
    name: str
    substation: str


# --- Request Schemas ---
class TransformerCreate(ComponentCreateBase):
    component_type: Literal[ComponentType.TRANSFORMER] = ComponentType.TRANSFORMER
    capacity_mva: float = Field(..., gt=0)
    voltage_kv: float = Field(..., gt=0)


class LineCreate(ComponentCreateBase):
    component_type: Literal[ComponentType.LINE] = ComponentType.LINE
    length_km: float = Field(..., gt=0)
    voltage_kv: float = Field(..., gt=0)


class SwitchCreate(ComponentCreateBase):
    component_type: Literal[ComponentType.SWITCH] = ComponentType.SWITCH
    status: SwitchStatus


ComponentCreate = Annotated[
    TransformerCreate | LineCreate | SwitchCreate, Field(discriminator="component_type")
]


class TransformerUpdate(ComponentUpdateBase):
    """Schema for updating a transformer."""

    component_type: Literal[ComponentType.TRANSFORMER] = ComponentType.TRANSFORMER
    capacity_mva: float | None = Field(None, gt=0)
    voltage_kv: float | None = Field(None, gt=0)


class LineUpdate(ComponentUpdateBase):
    """Schema for updating a line."""

    component_type: Literal[ComponentType.LINE] = ComponentType.LINE
    length_km: float | None = Field(None, gt=0)
    voltage_kv: float | None = Field(None, gt=0)


class SwitchUpdate(ComponentUpdateBase):
    """Schema for updating a switch."""

    component_type: Literal[ComponentType.SWITCH] = ComponentType.SWITCH
    status: SwitchStatus | None = None


ComponentUpdate = Annotated[
    TransformerUpdate | LineUpdate | SwitchUpdate, Field(discriminator="component_type")
]


# --- Response Schemas ---
class TransformerResponse(ComponentResponseBase):
    """Transformer response schema."""

    component_type: Literal[ComponentType.TRANSFORMER] = ComponentType.TRANSFORMER
    capacity_mva: float
    voltage_kv: float


class LineResponse(ComponentResponseBase):
    """Line response schema."""

    component_type: Literal[ComponentType.LINE] = ComponentType.LINE
    length_km: float
    voltage_kv: float


class SwitchResponse(ComponentResponseBase):
    """Switch response schema."""

    component_type: Literal[ComponentType.SWITCH] = ComponentType.SWITCH
    status: SwitchStatus


ComponentResponse = Annotated[
    TransformerResponse | LineResponse | SwitchResponse,
    Field(discriminator="component_type"),
]
