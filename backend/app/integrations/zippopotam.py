from dataclasses import dataclass
from decimal import Decimal

import httpx


class PostalCodeNotFoundError(ValueError):
    pass


class PostalCodeServiceError(RuntimeError):
    pass


@dataclass(frozen=True)
class PostalLocation:
    postal_code: str
    latitude: Decimal
    longitude: Decimal
    place_name: str | None


class ZippopotamClient:
    def __init__(self, base_url: str = "https://api.zippopotam.us", timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_location(self, postal_code: str) -> PostalLocation:
        try:
            response = httpx.get(
                f"{self.base_url}/mx/{postal_code}",
                timeout=self.timeout,
            )
        except httpx.RequestError as error:
            raise PostalCodeServiceError(
                "No pudimos validar los códigos postales. Intenta nuevamente en unos minutos."
            ) from error

        if response.status_code == 404:
            raise PostalCodeNotFoundError(
                f"No encontramos cobertura para el código postal {postal_code}."
            )
        try:
            response.raise_for_status()
            place = response.json()["places"][0]
            return PostalLocation(
                postal_code=postal_code,
                latitude=Decimal(str(place["latitude"])),
                longitude=Decimal(str(place["longitude"])),
                place_name=place.get("place name"),
            )
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise PostalCodeServiceError(
                "No pudimos validar los códigos postales. Intenta nuevamente en unos minutos."
            ) from error

