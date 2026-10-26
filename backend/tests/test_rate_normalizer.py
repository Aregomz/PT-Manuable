from decimal import Decimal

from app.services.rate_normalizer import normalize_carrier, normalize_rate, read_rate_csv

CARRIERS = {"dhl": 1, "fedex": 2, "estafeta": 3, "redpack": 4}


def rate_row(**overrides: str) -> dict[str, str]:
    row = {
        "paqueteria": "FEDEX",
        "zona": "zona3",
        "peso_min": "5000",
        "peso_max": "10000",
        "unidad": "g",
        "precio": "$1,137.24",
        "dias_entrega": "3-5",
        "vigencia_desde": "",
    }
    return {**row, **overrides}


def test_normalizes_safe_variations_without_inventing_values() -> None:
    result = normalize_rate(2, rate_row(), CARRIERS)

    assert result["status"] == "corrected"
    assert result["rate"]["carrier_id"] == 2
    assert result["rate"]["zone"] == 3
    assert result["rate"]["min_weight_kg"] == Decimal("5.000")
    assert result["rate"]["max_weight_kg"] == Decimal("10.000")
    assert result["rate"]["price_mxn"] == Decimal("1137.24")
    assert result["rate"]["min_delivery_days"] == 3
    assert result["rate"]["max_delivery_days"] == 5


def test_rejects_a_rate_without_price() -> None:
    result = normalize_rate(2, rate_row(precio=""), CARRIERS)

    assert result["status"] == "rejected"
    assert "no tiene precio" in result["reason"]


def test_rejects_suspicious_prices_for_commercial_confirmation() -> None:
    result = normalize_rate(2, rate_row(precio="42237.00"), CARRIERS)

    assert result["status"] == "rejected"
    assert "requiere confirmación" in result["reason"]


def test_rejects_inverted_weight_ranges() -> None:
    result = normalize_rate(
        2,
        rate_row(peso_min="5", peso_max="3", unidad="kg", precio="260.00"),
        CARRIERS,
    )

    assert result["status"] == "rejected"
    assert "invertido" in result["reason"]


def test_allows_missing_delivery_time_and_effective_date() -> None:
    result = normalize_rate(
        2,
        rate_row(dias_entrega="", vigencia_desde="", precio="933.12"),
        CARRIERS,
    )

    assert result["status"] == "corrected"
    assert result["rate"]["min_delivery_days"] is None
    assert result["rate"]["effective_from"] is None


def test_normalizes_a_carrier_and_preserves_its_inactive_state() -> None:
    result = normalize_carrier(
        2,
        {
            "carrier_id": " carr-04 ",
            "nombre": "RED PACK",
            "tipo_servicio": "terrestre",
            "activo": "no",
        },
        set(),
    )

    assert result["status"] == "corrected"
    assert result["carrier"]["code"] == "CARR-04"
    assert result["carrier"]["name"] == "Redpack"
    assert result["carrier"]["service_type"] == "Terrestre"
    assert result["carrier"]["is_active"] is False


def test_reads_the_phase_two_rate_format() -> None:
    rows = read_rate_csv(
        (
            b"paqueteria,zona,peso_min_kg,peso_max_kg,precio_mxn,dias_entrega,"
            b"vigencia_desde\nDHL,1,0,1,170.00,1-2,2026-12-01\n"
        ),
        "tarifas_dhl_v2.csv",
    )

    assert rows == [
        {
            "paqueteria": "DHL",
            "zona": "1",
            "peso_min": "0",
            "peso_max": "1",
            "unidad": "kg",
            "precio": "170.00",
            "dias_entrega": "1-2",
            "vigencia_desde": "2026-12-01",
        }
    ]
