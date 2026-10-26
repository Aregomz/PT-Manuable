from typing import Any

from app.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import CarrierUpdate, RateUpdate


class CatalogService:
    def __init__(self, repository: CatalogRepository) -> None:
        self.repository = repository

    def get_loaded_data(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "carriers": self.repository.list_carriers(),
            "rates": self.repository.list_rates(),
        }

    def update_carrier(self, carrier_id: int, update: CarrierUpdate) -> dict[str, Any] | None:
        return self.repository.update_carrier(
            carrier_id,
            name=update.name.strip(),
            service_type=update.service_type.strip(),
            is_active=update.is_active,
        )

    def update_rate(self, rate_id: int, update: RateUpdate) -> dict[str, Any] | None:
        return self.repository.update_rate(rate_id, **update.model_dump())
