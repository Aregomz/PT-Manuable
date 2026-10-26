import math
from datetime import UTC, datetime, timedelta
from decimal import ROUND_CEILING, Decimal
from typing import Protocol
from uuid import uuid4

from app.integrations.zippopotam import PostalLocation
from app.repositories.quote_repository import QuoteRepository


class PostalClient(Protocol):
    def get_location(self, postal_code: str) -> PostalLocation: ...


class QuoteService:
    def __init__(self, repository: QuoteRepository, postal_client: PostalClient) -> None:
        self.repository = repository
        self.postal_client = postal_client

    def create_quote(
        self,
        email: str,
        origin_postal_code: str,
        destination_postal_code: str,
        weight_kg: Decimal,
        length_cm: Decimal | None = None,
        width_cm: Decimal | None = None,
        height_cm: Decimal | None = None,
        quoted_at: datetime | None = None,
    ) -> dict[str, object]:
        quote_time = quoted_at or datetime.now(UTC)
        dimensions = (length_cm, width_cm, height_cm)
        if any(value is not None for value in dimensions) and not all(
            value is not None for value in dimensions
        ):
            raise ValueError("Debes indicar largo, ancho y alto del paquete.")
        volumetric_weight = calculate_volumetric_weight(length_cm, width_cm, height_cm)
        origin = self._get_location(origin_postal_code)
        destination = self._get_location(destination_postal_code)
        distance_km = calculate_distance_km(origin, destination)
        zone = calculate_zone(distance_km)
        rates = self.repository.find_rates(zone, weight_kg, volumetric_weight, quote_time.date())

        lead_id = self.repository.upsert_lead(email.strip().lower())
        quote = {
                "origin_postal_code": origin_postal_code,
                "destination_postal_code": destination_postal_code,
                "weight_kg": weight_kg,
                "external_reference": f"WEB-{uuid4().hex[:12].upper()}",
                "length_cm": length_cm,
                "width_cm": width_cm,
                "height_cm": height_cm,
                "volumetric_weight_kg": volumetric_weight,
                "origin_latitude": origin.latitude,
                "origin_longitude": origin.longitude,
                "destination_latitude": destination.latitude,
                "destination_longitude": destination.longitude,
                "distance_km": distance_km,
                "zone": zone,
                "quoted_at": quote_time,
                "valid_until": quote_time + timedelta(days=30),
        }
        quote_id = self.repository.create_quote(lead_id, quote)
        self.repository.save_options(quote_id, rates)
        return {
            "id": quote_id,
            "external_reference": quote["external_reference"],
            "email": email.strip().lower(),
            "origin_postal_code": origin_postal_code,
            "origin_place_name": origin.place_name,
            "destination_postal_code": destination_postal_code,
            "destination_place_name": destination.place_name,
            "weight_kg": weight_kg,
            "length_cm": length_cm,
            "width_cm": width_cm,
            "height_cm": height_cm,
            "volumetric_weight_kg": volumetric_weight,
            "distance_km": distance_km,
            "zone": zone,
            "quoted_at": quote_time,
            "valid_until": quote_time + timedelta(days=30),
            "options": rates,
        }

    def _get_location(self, postal_code: str) -> PostalLocation:
        cached = self.repository.find_postal_code(postal_code)
        if cached:
            return PostalLocation(
                postal_code=postal_code,
                latitude=cached["latitude"],
                longitude=cached["longitude"],
                place_name=cached["place_name"],
            )
        location = self.postal_client.get_location(postal_code)
        self.repository.save_postal_code(location)
        return location


def calculate_distance_km(origin: PostalLocation, destination: PostalLocation) -> Decimal:
    earth_radius_km = 6371.0088
    origin_latitude = math.radians(float(origin.latitude))
    destination_latitude = math.radians(float(destination.latitude))
    latitude_delta = destination_latitude - origin_latitude
    longitude_delta = math.radians(float(destination.longitude - origin.longitude))
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(origin_latitude)
        * math.cos(destination_latitude)
        * math.sin(longitude_delta / 2) ** 2
    )
    distance = 2 * earth_radius_km * math.asin(math.sqrt(haversine))
    return Decimal(str(round(distance, 2)))


def calculate_zone(distance_km: Decimal) -> int:
    if distance_km <= 100:
        return 1
    if distance_km <= 500:
        return 2
    if distance_km <= 1000:
        return 3
    return 4


def calculate_volumetric_weight(
    length_cm: Decimal | None,
    width_cm: Decimal | None,
    height_cm: Decimal | None,
) -> Decimal | None:
    if length_cm is None or width_cm is None or height_cm is None:
        return None
    weight = length_cm * width_cm * height_cm / Decimal(5000)
    return weight.quantize(Decimal("0.001"), rounding=ROUND_CEILING)

