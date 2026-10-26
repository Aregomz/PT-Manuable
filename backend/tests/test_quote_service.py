from decimal import Decimal
from unittest.mock import Mock

from app.integrations.zippopotam import PostalLocation
from app.schemas.quotes import QuoteRequest
from app.services.quote_service import (
    QuoteService,
    calculate_distance_km,
    calculate_volumetric_weight,
    calculate_zone,
)


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


def test_trims_external_spaces_from_postal_codes() -> None:
    request = QuoteRequest(
        email="cliente@example.com",
        origin_postal_code=" 06600 ",
        destination_postal_code="64000 ",
        weight_kg="1",
    )

    assert request.origin_postal_code == "06600"
    assert request.destination_postal_code == "64000"


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


def test_calculates_volumetric_weight_rounding_up_to_grams() -> None:
    assert calculate_volumetric_weight(
        Decimal("33.3"), Decimal("22.2"), Decimal("11.1")
    ) == Decimal("1.642")


def test_uses_dimensions_to_find_rates_and_keeps_a_thirty_day_snapshot() -> None:
    repository = Mock()
    repository.find_postal_code.return_value = None
    repository.find_rates.return_value = []
    repository.upsert_lead.return_value = 4
    repository.create_quote.return_value = 8
    postal_client = Mock()
    postal_client.get_location.side_effect = [
        location("06600", "19.385", "-99.160", "Juarez"),
        location("64000", "25.8512", "-100.309", "Monterrey Centro"),
    ]

    result = QuoteService(repository, postal_client).create_quote(
        "cliente@example.com",
        "06600",
        "64000",
        Decimal("1"),
        Decimal("50"),
        Decimal("40"),
        Decimal("30"),
    )

    assert result["volumetric_weight_kg"] == Decimal("12.000")
    assert (result["valid_until"] - result["quoted_at"]).days == 30
    repository.find_rates.assert_called_once()
    assert repository.find_rates.call_args.args[2] == Decimal("12.000")

