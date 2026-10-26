from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class QuoteRequest(BaseModel):
    email: EmailStr
    origin_postal_code: str = Field(pattern=r"^[0-9]{5}$")
    destination_postal_code: str = Field(pattern=r"^[0-9]{5}$")
    weight_kg: Decimal = Field(gt=0)


class QuoteOptionResponse(BaseModel):
    rate_id: int
    carrier_id: int
    carrier_name: str
    price_mxn: Decimal
    min_delivery_days: int | None
    max_delivery_days: int | None


class QuoteResponse(BaseModel):
    id: int
    email: EmailStr
    origin_postal_code: str
    origin_place_name: str | None
    destination_postal_code: str
    destination_place_name: str | None
    weight_kg: Decimal
    distance_km: Decimal
    zone: int
    options: list[QuoteOptionResponse]

