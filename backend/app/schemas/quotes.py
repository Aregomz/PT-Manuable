from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class QuoteRequest(BaseModel):
    email: EmailStr
    origin_postal_code: str = Field(pattern=r"^[0-9]{5}$")
    destination_postal_code: str = Field(pattern=r"^[0-9]{5}$")
    weight_kg: Decimal = Field(gt=0)
    length_cm: Decimal | None = Field(default=None, gt=0)
    width_cm: Decimal | None = Field(default=None, gt=0)
    height_cm: Decimal | None = Field(default=None, gt=0)

    @field_validator("origin_postal_code", "destination_postal_code", mode="before")
    @classmethod
    def normalize_postal_code(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class QuoteOptionResponse(BaseModel):
    rate_id: int
    carrier_id: int
    carrier_name: str
    price_mxn: Decimal
    min_delivery_days: int | None
    max_delivery_days: int | None
    actual_weight_kg: Decimal
    volumetric_weight_kg: Decimal | None
    billable_weight_kg: Decimal


class QuoteResponse(BaseModel):
    id: int
    external_reference: str
    email: EmailStr
    origin_postal_code: str
    origin_place_name: str | None
    destination_postal_code: str
    destination_place_name: str | None
    weight_kg: Decimal
    length_cm: Decimal | None
    width_cm: Decimal | None
    height_cm: Decimal | None
    volumetric_weight_kg: Decimal | None
    distance_km: Decimal
    zone: int
    quoted_at: datetime
    valid_until: datetime
    options: list[QuoteOptionResponse]

