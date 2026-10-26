from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class CarrierResponse(BaseModel):
    id: int
    code: str
    name: str
    service_type: str
    is_active: bool
    updated_at: datetime


class RateResponse(BaseModel):
    id: int
    carrier_name: str
    carrier_is_active: bool
    zone: int
    min_weight_kg: Decimal
    max_weight_kg: Decimal
    price_mxn: Decimal
    min_delivery_days: int | None
    max_delivery_days: int | None
    effective_from: date | None


class LoadedDataResponse(BaseModel):
    carriers: list[CarrierResponse]
    rates: list[RateResponse]


class CarrierUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    service_type: str = Field(min_length=1, max_length=50)
    is_active: bool


class RateUpdate(BaseModel):
    zone: int = Field(ge=1, le=4)
    min_weight_kg: Decimal = Field(ge=0)
    max_weight_kg: Decimal = Field(gt=0)
    price_mxn: Decimal = Field(gt=0)
    min_delivery_days: int | None = Field(default=None, gt=0)
    max_delivery_days: int | None = Field(default=None, gt=0)
    effective_from: date | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> "RateUpdate":
        if self.max_weight_kg <= self.min_weight_kg:
            raise ValueError("El peso máximo debe ser mayor que el peso mínimo.")
        if (self.min_delivery_days is None) != (self.max_delivery_days is None):
            raise ValueError("Los dos tiempos de entrega deben indicarse o dejarse vacíos.")
        if (
            self.min_delivery_days is not None
            and self.max_delivery_days is not None
            and self.max_delivery_days < self.min_delivery_days
        ):
            raise ValueError("El tiempo máximo debe ser mayor o igual al mínimo.")
        return self
