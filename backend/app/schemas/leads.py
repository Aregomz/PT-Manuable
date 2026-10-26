from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class LeadQuoteResponse(BaseModel):
    id: int
    origin_postal_code: str
    destination_postal_code: str
    weight_kg: Decimal
    distance_km: Decimal
    zone: int
    option_count: int
    created_at: datetime


class CapturedLeadResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    quotes: list[LeadQuoteResponse]


class CapturedLeadsResponse(BaseModel):
    leads: list[CapturedLeadResponse]

