from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class LeadQuoteOptionResponse(BaseModel):
    carrier_name: str
    price_mxn: Decimal
    min_delivery_days: int | None
    max_delivery_days: int | None
    billable_weight_kg: Decimal


class LeadQuoteResponse(BaseModel):
    id: int
    external_reference: str
    source: str
    origin_postal_code: str
    destination_postal_code: str
    weight_kg: Decimal
    distance_km: Decimal | None
    zone: int
    option_count: int
    options: list[LeadQuoteOptionResponse]
    quoted_at: datetime
    valid_until: datetime


class DailyQuoteMetricResponse(BaseModel):
    date: date
    total_quotes: int
    without_options: int


class CapturedLeadResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    quotes: list[LeadQuoteResponse]


class CapturedLeadsResponse(BaseModel):
    leads: list[CapturedLeadResponse]
    daily_metrics: list[DailyQuoteMetricResponse]

