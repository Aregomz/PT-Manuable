from datetime import date
from decimal import Decimal

from app.services.historical_quote_import_service import normalize_historical_quote


def test_normalizes_a_historical_quote_as_an_immutable_snapshot() -> None:
    result = normalize_historical_quote(
        2,
        {
            "cotizacion_id": "cot-0101",
            "fecha": "2026-11-09",
            "correo": "CLIENTE@example.com",
            "cp_origen": "06600",
            "cp_destino": "64000",
            "zona": "Zona 3",
            "peso_kg": "2.5",
            "paqueteria": "DHL Express",
            "precio_cotizado": "422.37",
        },
        {"dhl": {"id": 1, "name": "DHL"}},
    )

    assert result["status"] == "loaded"
    assert result["quote"]["external_reference"] == "COT-0101"
    assert result["quote"]["email"] == "cliente@example.com"
    assert result["quote"]["weight_kg"] == Decimal("2.500")
    assert result["quote"]["price_mxn"] == Decimal("422.37")
    assert result["quote"]["quoted_at"].date() == date(2026, 11, 9)
    assert (result["quote"]["valid_until"] - result["quote"]["quoted_at"]).days == 30


def test_rejects_city_names_in_postal_code_columns() -> None:
    result = normalize_historical_quote(
        2,
        {
            "cotizacion_id": "COT-0102",
            "fecha": "2026-11-09",
            "correo": "cliente@example.com",
            "cp_origen": "Monterrey",
            "cp_destino": "64000",
            "zona": "3",
            "peso_kg": "2.5",
            "paqueteria": "DHL",
            "precio_cotizado": "422.37",
        },
        {"dhl": {"id": 1, "name": "DHL"}},
    )

    assert result["status"] == "rejected"
    assert "cinco dígitos" in result["reason"]
