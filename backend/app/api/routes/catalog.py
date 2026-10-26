from fastapi import APIRouter, HTTPException, status
from psycopg import IntegrityError

from app.api.dependencies import CommercialUser
from app.db import get_connection
from app.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import (
    CarrierResponse,
    CarrierUpdate,
    LoadedDataResponse,
    RateResponse,
    RateUpdate,
)
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/admin/data", tags=["catalog"])


@router.get("", response_model=LoadedDataResponse)
def get_loaded_data(_: CommercialUser) -> LoadedDataResponse:
    with get_connection() as connection:
        result = CatalogService(CatalogRepository(connection)).get_loaded_data()
    return LoadedDataResponse.model_validate(result)


@router.put("/carriers/{carrier_id}", response_model=CarrierResponse)
def update_carrier(
    carrier_id: int,
    update: CarrierUpdate,
    _: CommercialUser,
) -> CarrierResponse:
    try:
        with get_connection() as connection:
            result = CatalogService(CatalogRepository(connection)).update_carrier(
                carrier_id, update
            )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una paquetería con ese nombre.",
        ) from error
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paquetería no encontrada.",
        )
    return CarrierResponse.model_validate(result)


@router.put("/rates/{rate_id}", response_model=RateResponse)
def update_rate(rate_id: int, update: RateUpdate, _: CommercialUser) -> RateResponse:
    try:
        with get_connection() as connection:
            result = CatalogService(CatalogRepository(connection)).update_rate(rate_id, update)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La edición coincide con otra tarifa existente.",
        ) from error
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarifa no encontrada.")
    return RateResponse.model_validate(result)
