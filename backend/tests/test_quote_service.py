from decimal import Decimal
from unittest.mock import Mock

from app.integrations.zippopotam import PostalLocation
from app.services.quote_service import QuoteService, calculate_distance_km, calculate_zone


def location(postal_code: str, latitude: str, longitude: str, name: str) -> PostalLocation:
    return PostalLocation(
        postal_code=postal_code,
        latitude=Decimal(latitude),
        longitude=Decimal(longitude),
        place_name=name,
    )


def test_calculates_distance_and_zone() -> None:
    origin = location("06600", "19.385", "-99.160", "Juarez")
    destination = location("64000", "25.8512", "-100.309", "Monterrey Centro")

    distance = calculate_distance_km(origin, destination)

    assert Decimal("700") < distance < Decimal("800")
    assert calculate_zone(distance) == 3


def test_creates_a_lead_quote_and_snapshots_available_options() -> None:
    repository = Mock()
    repository.find_postal_code.return_value = None
    repository.find_rates.return_value = [
        {
            "rate_id": 10,
            "carrier_id": 3,
            "carrier_name": "Estafeta",
            "price_mxn": Decimal("309.74"),
            "min_delivery_days": 5,
            "max_delivery_days": 7,
        }
    ]
    repository.upsert_lead.return_value = 4
    repository.create_quote.return_value = 8
    postal_client = Mock()
    postal_client.get_location.side_effect = [
        location("06600", "19.385", "-99.160", "Juarez"),
        location("64000", "25.8512", "-100.309", "Monterrey Centro"),
    ]

    result = QuoteService(repository, postal_client).create_quote(
        "CLIENTE@EXAMPLE.COM",
        "06600",
        "64000",
        Decimal("1.84"),
    )

    assert result["id"] == 8
    assert result["email"] == "cliente@example.com"
    assert result["zone"] == 3
    assert len(result["options"]) == 1
    repository.save_options.assert_called_once_with(8, repository.find_rates.return_value)

