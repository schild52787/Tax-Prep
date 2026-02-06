from datetime import datetime

from pydantic import BaseModel, Field

from app.models.tax_return import FilingStatus, ReturnStatus


class TaxReturnCreate(BaseModel):
    return_name: str = Field(..., min_length=1, max_length=200)
    tax_year: int = Field(default=2025, ge=2024, le=2025)
    filing_status: FilingStatus = FilingStatus.SINGLE


class TaxReturnUpdate(BaseModel):
    return_name: str | None = None
    filing_status: FilingStatus | None = None
    status: ReturnStatus | None = None


class TaxReturnResponse(BaseModel):
    id: str
    return_name: str
    tax_year: int
    filing_status: FilingStatus
    status: ReturnStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaxReturnSummary(BaseModel):
    id: str
    return_name: str
    tax_year: int
    filing_status: FilingStatus
    status: ReturnStatus
    created_at: datetime

    model_config = {"from_attributes": True}
