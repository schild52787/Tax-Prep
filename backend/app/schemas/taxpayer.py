from datetime import date

from pydantic import BaseModel, Field

from app.models.taxpayer import TaxpayerRole


class TaxpayerCreate(BaseModel):
    first_name: str | None = Field(None, max_length=50)
    middle_initial: str | None = Field(None, max_length=1)
    last_name: str | None = Field(None, max_length=50)
    ssn: str | None = Field(None, pattern=r"^\d{3}-?\d{2}-?\d{4}$")
    date_of_birth: date | None = None
    occupation: str | None = Field(None, max_length=100)
    street_address: str | None = Field(None, max_length=200)
    apt_number: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, pattern=r"^[A-Z]{2}$")
    zip_code: str | None = Field(None, pattern=r"^\d{5}(-\d{4})?$")


class TaxpayerUpdate(TaxpayerCreate):
    pass


class TaxpayerResponse(BaseModel):
    id: str
    return_id: str
    role: TaxpayerRole
    first_name: str | None
    middle_initial: str | None
    last_name: str | None
    date_of_birth: date | None
    occupation: str | None
    street_address: str | None
    apt_number: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    # SSN is never returned in responses

    model_config = {"from_attributes": True}


class DependentCreate(BaseModel):
    first_name: str | None = Field(None, max_length=50)
    last_name: str | None = Field(None, max_length=50)
    ssn: str | None = Field(None, pattern=r"^\d{3}-?\d{2}-?\d{4}$")
    relationship_to_taxpayer: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    months_lived_with: int | None = Field(None, ge=0, le=12)
    is_student: bool = False
    is_disabled: bool = False


class DependentUpdate(DependentCreate):
    pass


class DependentResponse(BaseModel):
    id: str
    return_id: str
    first_name: str | None
    last_name: str | None
    relationship_to_taxpayer: str | None
    date_of_birth: date | None
    months_lived_with: int | None
    is_student: bool
    is_disabled: bool

    model_config = {"from_attributes": True}
