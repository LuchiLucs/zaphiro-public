"""Report API schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from core.models import FinalReportSchema


class ReportRequest(BaseModel):
    start_date: datetime
    end_date: datetime


class ReportResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportDetailResponse(ReportResponse):
    # Instead of a raw string, we use the actual domain schema
    result_json: FinalReportSchema | None = None
