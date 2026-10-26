from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.dependencies import CommercialUser
from app.db import get_connection
from app.repositories.import_repository import ImportRepository
from app.schemas.imports import ImportSummaryResponse
from app.services.historical_quote_import_service import HistoricalQuoteImportService
from app.services.rate_import_service import RateImportService
from app.services.rate_normalizer import CsvValidationError

router = APIRouter(prefix="/api/admin/imports", tags=["imports"])
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/carriers", response_model=ImportSummaryResponse, status_code=status.HTTP_201_CREATED)
async def import_carriers(
    _: CommercialUser,
    carriers_file: Annotated[UploadFile, File()],
) -> ImportSummaryResponse:
    carriers_content = await read_csv_upload(carriers_file, "paqueterías")

    try:
        with get_connection() as connection, connection.transaction():
            service = RateImportService(ImportRepository(connection))
            result = service.import_carriers(
                carriers_file.filename or "paqueterias.csv",
                carriers_content,
            )
    except CsvValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return ImportSummaryResponse.model_validate(result)


@router.post("/rates", response_model=ImportSummaryResponse, status_code=status.HTTP_201_CREATED)
async def import_rates(
    _: CommercialUser,
    rates_file: Annotated[UploadFile, File()],
) -> ImportSummaryResponse:
    rates_content = await read_csv_upload(rates_file, "tarifas")

    try:
        with get_connection() as connection, connection.transaction():
            service = RateImportService(ImportRepository(connection))
            result = service.import_rates(
                rates_file.filename or "tarifas.csv",
                rates_content,
            )
    except CsvValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return ImportSummaryResponse.model_validate(result)


@router.post(
    "/historical-quotes",
    response_model=ImportSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_historical_quotes(
    _: CommercialUser,
    quotes_file: Annotated[UploadFile, File()],
) -> ImportSummaryResponse:
    quotes_content = await read_csv_upload(quotes_file, "cotizaciones históricas")
    try:
        with get_connection() as connection, connection.transaction():
            result = HistoricalQuoteImportService(ImportRepository(connection)).import_quotes(
                quotes_file.filename or "cotizaciones_historicas.csv",
                quotes_content,
            )
    except CsvValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return ImportSummaryResponse.model_validate(result)


async def read_csv_upload(upload: UploadFile, label: str) -> bytes:
    filename = upload.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El archivo de {label} debe tener extensión .csv.",
        )
    content = await upload.read(MAX_FILE_SIZE + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El archivo de {label} está vacío.",
        )
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo de {label} supera el límite de 5 MB.",
        )
    return content
