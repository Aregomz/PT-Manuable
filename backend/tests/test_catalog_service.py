from unittest.mock import Mock

from app.schemas.catalog import CarrierUpdate, RateUpdate
from app.services.catalog_service import CatalogService


def test_updates_a_carrier_with_normalized_text() -> None:
    repository = Mock()
    repository.update_carrier.return_value = {"id": 1}

    result = CatalogService(repository).update_carrier(
        1,
        CarrierUpdate(name="  Estafeta ", service_type=" Terrestre ", is_active=False),
    )

    assert result == {"id": 1}
    repository.update_carrier.assert_called_once_with(
        1,
        name="Estafeta",
        service_type="Terrestre",
        is_active=False,
        volumetric_divisor=None,
        volumetric_effective_from=None,
    )


def test_updates_a_rate_with_validated_ranges() -> None:
    repository = Mock()
    repository.update_rate.return_value = {"id": 3}
    update = RateUpdate(
        zone=2,
        min_weight_kg="1.01",
        max_weight_kg="3",
        price_mxn="250",
        min_delivery_days=2,
        max_delivery_days=4,
    )

    assert CatalogService(repository).update_rate(3, update) == {"id": 3}
    repository.update_rate.assert_called_once_with(3, **update.model_dump())
