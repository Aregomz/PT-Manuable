import hashlib
import re
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.repositories.import_repository import ImportRepository
from app.services.rate_normalizer import (
    ALIASES,
    CsvValidationError,
    normalize_key,
    parse_date,
    parse_zone,
    read_csv,
)

EXPECTED_HEADERS = {
    "cotizacion_id",
    "fecha",
    "correo",
    "cp_origen",
    "cp_destino",
    "zona",
    "peso_kg",
    "paqueteria",
    "precio_cotizado",
}
email_adapter = TypeAdapter(EmailStr)


class HistoricalQuoteImportService:
    def __init__(self, repository: ImportRepository) -> None:
        self.repository = repository

    def import_quotes(self, filename: str, content: bytes) -> dict[str, Any]:
        checksum = hashlib.sha256(b"historical-quotes\0" + content).hexdigest()
        existing = self.repository.find_by_checksum(checksum)
        if existing:
            result = self.repository.get_import(int(existing["id"]))
            result["already_imported"] = True
            return result

        raw_rows = read_csv(content, EXPECTED_HEADERS, filename)
        if not raw_rows:
            raise CsvValidationError("El archivo de cotizaciones históricas está vacío.")
        carriers = {
            ALIASES.get(normalize_key(str(row["name"])), normalize_key(str(row["name"]))): row
            for row in self.repository.get_carriers()
        }
        rows = [
            normalize_historical_quote(number, raw, carriers)
            for number, raw in enumerate(raw_rows, start=2)
        ]
        import_id = self.repository.create_import(filename, checksum, len(raw_rows))
        seen_references: set[str] = set()

        for row in rows:
            quote = row["quote"]
            if quote is not None and quote["external_reference"] in seen_references:
                row["status"] = "duplicate"
                row["reason"] = "El identificador ya apareció antes en este archivo."
                row["quote"] = None
            elif quote is not None:
                seen_references.add(quote["external_reference"])

            import_row_id = self.repository.add_import_row(import_id, row)
            if row["quote"] is None:
                continue
            quote["lead_id"] = self.repository.upsert_lead(quote.pop("email"))
            if not self.repository.add_historical_quote(import_row_id, quote):
                row["status"] = "duplicate"
                row["reason"] = "La cotización ya existe en la base de datos."
                self.repository.update_row_status(import_row_id, "duplicate", row["reason"])

        self.repository.complete_import(import_id, self._counts(rows))
        result = self.repository.get_import(import_id)
        result["already_imported"] = False
        return result

    @staticmethod
    def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            status: sum(row["status"] == status for row in rows)
            for status in ("loaded", "corrected", "rejected", "duplicate")
        }


def normalize_historical_quote(
    row_number: int,
    raw: dict[str, str],
    carriers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    try:
        reference = raw["cotizacion_id"].strip().upper()
        if not re.fullmatch(r"COT-[0-9]{4,}", reference):
            raise CsvValidationError("El identificador de cotización no tiene un formato válido.")
        try:
            email = str(email_adapter.validate_python(raw["correo"])).lower()
        except ValidationError as error:
            raise CsvValidationError("El correo no tiene un formato válido.") from error
        for field in ("cp_origen", "cp_destino"):
            if not re.fullmatch(r"[0-9]{5}", raw[field]):
                raise CsvValidationError(f"{field} debe contener cinco dígitos.")
        quote_date = parse_date(raw["fecha"])
        if quote_date is None:
            raise CsvValidationError("Falta la fecha de cotización.")
        quoted_at = datetime.combine(quote_date, time.min, tzinfo=UTC)
        zone = parse_zone(raw["zona"])
        try:
            weight = Decimal(raw["peso_kg"])
            price = Decimal(raw["precio_cotizado"])
        except InvalidOperation as error:
            raise CsvValidationError("El peso o el precio no es numérico.") from error
        if weight <= 0 or price <= 0:
            raise CsvValidationError("El peso y el precio deben ser mayores que cero.")
        carrier_key = ALIASES.get(
            normalize_key(raw["paqueteria"]), normalize_key(raw["paqueteria"])
        )
        carrier = carriers.get(carrier_key)
        if carrier is None:
            raise CsvValidationError("La paquetería no existe en el catálogo cargado.")
        quote = {
            "external_reference": reference,
            "email": email,
            "origin_postal_code": raw["cp_origen"],
            "destination_postal_code": raw["cp_destino"],
            "zone": zone,
            "weight_kg": weight.quantize(Decimal("0.001")),
            "carrier_id": int(carrier["id"]),
            "carrier_name": str(carrier["name"]),
            "price_mxn": price.quantize(Decimal("0.01")),
            "quoted_at": quoted_at,
            "valid_until": quoted_at + timedelta(days=30),
        }
        return {
            "row_number": row_number,
            "status": "loaded",
            "raw_data": raw,
            "normalized_data": {**quote, "email": email},
            "changes": [],
            "reason": None,
            "quote": quote,
            "rate": None,
        }
    except CsvValidationError as error:
        return {
            "row_number": row_number,
            "status": "rejected",
            "raw_data": raw,
            "normalized_data": None,
            "changes": [],
            "reason": str(error),
            "quote": None,
            "rate": None,
        }
