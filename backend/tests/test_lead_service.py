from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

from app.services.lead_service import LeadService


def test_groups_multiple_quotes_under_the_same_lead() -> None:
    created_at = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
    repository = Mock()
    repository.list_leads_with_quotes.return_value = [
        {
            "lead_id": 1,
            "email": "cliente@example.com",
            "lead_created_at": created_at,
            "quote_id": quote_id,
            "origin_postal_code": "06600",
            "destination_postal_code": "64000",
            "weight_kg": Decimal("2.000"),
            "distance_km": Decimal("900.00"),
            "zone": 3,
            "quote_created_at": created_at,
            "option_count": 2,
        }
        for quote_id in (2, 1)
    ]

    result = LeadService(repository).list_captured_leads()

    assert len(result["leads"]) == 1
    assert result["leads"][0]["email"] == "cliente@example.com"
    assert [quote["id"] for quote in result["leads"][0]["quotes"]] == [2, 1]

