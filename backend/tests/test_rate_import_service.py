from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.services.rate_import_service import RateImportService


@pytest.mark.parametrize("method_name", ["import_carriers", "import_rates"])
def test_an_identical_file_returns_the_original_report_without_processing(
    method_name: str,
) -> None:
    repository = Mock()
    repository.find_by_checksum.return_value = {"id": 7}
    repository.get_import.return_value = {"id": 7, "filename": "datos.csv"}
    service = RateImportService(repository)

    result = getattr(service, method_name)("datos.csv", b"same-content")

    assert result["already_imported"] is True
    repository.get_import.assert_called_once_with(7)
    repository.create_import.assert_not_called()


def test_rejects_overlapping_ranges_in_the_same_scope() -> None:
    rows = [
        rate_row(40, "3", "6", "470.00"),
        rate_row(74, "3", "5", "565.76"),
    ]

    RateImportService._reject_ambiguous_overlaps(rows)

    assert [row["status"] for row in rows] == ["rejected", "rejected"]
    assert "fila 74" in rows[0]["reason"]
    assert "fila 40" in rows[1]["reason"]
    assert all(row["rate"] is None for row in rows)


def rate_row(row_number: int, minimum: str, maximum: str, price: str) -> dict:
    return {
        "row_number": row_number,
        "status": "loaded",
        "reason": None,
        "normalized_data": {},
        "rate": {
            "carrier_id": 1,
            "zone": 2,
            "min_weight_kg": Decimal(minimum),
            "max_weight_kg": Decimal(maximum),
            "price_mxn": Decimal(price),
            "effective_from": None,
        },
    }

