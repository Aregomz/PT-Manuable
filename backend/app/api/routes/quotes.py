from fastapi import APIRouter, HTTPException, status

from app.db import get_connection
from app.integrations.zippopotam import (
    PostalCodeNotFoundError,
    PostalCodeServiceError,
    ZippopotamClient,
)
from app.repositories.quote_repository import QuoteRepository
from app.schemas.quotes import QuoteRequest, QuoteResponse
from app.services.quote_service import QuoteService

router = APIRouter(prefix="/api/quotes", tags=["quotes"])


@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(request: QuoteRequest) -> QuoteResponse:
    try:
        with get_connection() as connection, connection.transaction():
            result = QuoteService(
                QuoteRepository(connection),
                ZippopotamClient(),
            ).create_quote(
                str(request.email),
                request.origin_postal_code,
                request.destination_postal_code,
                request.weight_kg,
                request.length_cm,
                request.width_cm,
                request.height_cm,
            )
    except PostalCodeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except PostalCodeServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return QuoteResponse.model_validate(result)

