from typing import Any

from app.repositories.lead_repository import LeadRepository


class LeadService:
    def __init__(self, repository: LeadRepository) -> None:
        self.repository = repository

    def list_captured_leads(self) -> dict[str, list[dict[str, Any]]]:
        leads: dict[int, dict[str, Any]] = {}
        for row in self.repository.list_leads_with_quotes():
            lead_id = int(row["lead_id"])
            lead = leads.setdefault(
                lead_id,
                {
                    "id": lead_id,
                    "email": row["email"],
                    "created_at": row["lead_created_at"],
                    "quotes": [],
                },
            )
            if row["quote_id"] is not None:
                lead["quotes"].append(
                    {
                        "id": row["quote_id"],
                        "external_reference": row["external_reference"],
                        "source": row["source"],
                        "origin_postal_code": row["origin_postal_code"],
                        "destination_postal_code": row["destination_postal_code"],
                        "weight_kg": row["weight_kg"],
                        "distance_km": row["distance_km"],
                        "zone": row["zone"],
                        "option_count": row["option_count"],
                        "options": row["options"],
                        "quoted_at": row["quoted_at"],
                        "valid_until": row["valid_until"],
                    }
                )
        return {
            "leads": list(leads.values()),
            "daily_metrics": self.repository.list_daily_metrics(),
        }

