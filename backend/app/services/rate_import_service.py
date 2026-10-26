import hashlib
from typing import Any

from app.repositories.import_repository import ImportRepository
from app.services.rate_normalizer import (
    ALIASES,
    EXPECTED_CARRIER_HEADERS,
    EXPECTED_RATE_HEADERS,
    CsvValidationError,
    normalize_carrier,
    normalize_key,
    normalize_rate,
    read_csv,
)


class RateImportService:
    def __init__(self, repository: ImportRepository) -> None:
        self.repository = repository

    def import_carriers(self, filename: str, content: bytes) -> dict[str, Any]:
        checksum = hashlib.sha256(b"carriers\0" + content).hexdigest()
        existing = self.repository.find_by_checksum(checksum)
        if existing:
            result = self.repository.get_import(int(existing["id"]))
            result["already_imported"] = True
            return result

        raw_rows = read_csv(content, EXPECTED_CARRIER_HEADERS, filename)
        if not raw_rows:
            raise CsvValidationError("El archivo de paqueterías no contiene registros.")
        seen_codes: set[str] = set()
        normalized_rows = [
            normalize_carrier(row_number, raw, seen_codes)
            for row_number, raw in enumerate(raw_rows, start=2)
        ]
        import_id = self.repository.create_import(filename, checksum, len(raw_rows))

        for row in normalized_rows:
            self.repository.add_import_row(import_id, row)
            if row.get("carrier") is not None:
                self.repository.upsert_carrier(row["carrier"])

        self.repository.complete_import(import_id, self._counts(normalized_rows))
        result = self.repository.get_import(import_id)
        result["already_imported"] = False
        return result

    def import_rates(self, filename: str, content: bytes) -> dict[str, Any]:
        checksum = hashlib.sha256(b"rates\0" + content).hexdigest()
        existing = self.repository.find_by_checksum(checksum)
        if existing:
            result = self.repository.get_import(int(existing["id"]))
            result["already_imported"] = True
            return result

        raw_rows = read_csv(content, EXPECTED_RATE_HEADERS, filename)
        if not raw_rows:
            raise CsvValidationError("El archivo de tarifas no contiene registros.")
        carrier_ids = {
            ALIASES.get(normalize_key(str(row["name"])), normalize_key(str(row["name"]))): int(
                row["id"]
            )
            for row in self.repository.get_carriers()
        }
        normalized_rows = [
            normalize_rate(row_number, raw, carrier_ids)
            for row_number, raw in enumerate(raw_rows, start=2)
        ]
        self._reject_ambiguous_overlaps(normalized_rows)
        import_id = self.repository.create_import(filename, checksum, len(raw_rows))
        seen_keys: set[tuple[Any, ...]] = set()

        for row in normalized_rows:
            rate = row["rate"]
            if rate is not None:
                key = (
                    rate["carrier_id"],
                    rate["zone"],
                    rate["min_weight_kg"],
                    rate["max_weight_kg"],
                    rate["effective_from"],
                )
                if key in seen_keys:
                    row["status"] = "duplicate"
                    row["reason"] = "La misma tarifa ya apareció antes en este archivo."
                    row["rate"] = None
                else:
                    seen_keys.add(key)

            import_row_id = self.repository.add_import_row(import_id, row)
            if row["rate"] is not None and not self.repository.add_rate(import_row_id, row["rate"]):
                row["status"] = "duplicate"
                row["reason"] = "La tarifa ya existe en la base de datos."
                self.repository.update_row_status(import_row_id, "duplicate", row["reason"])

        self.repository.complete_import(import_id, self._counts(normalized_rows))
        result = self.repository.get_import(import_id)
        result["already_imported"] = False
        return result

    @staticmethod
    def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            status: sum(row["status"] == status for row in rows)
            for status in ("loaded", "corrected", "rejected", "duplicate")
        }

    @staticmethod
    def _reject_ambiguous_overlaps(rows: list[dict[str, Any]]) -> None:
        conflicts: dict[int, list[int]] = {}
        for index, first_row in enumerate(rows):
            first = first_row.get("rate")
            if first is None:
                continue
            for second_row in rows[index + 1 :]:
                second = second_row.get("rate")
                if second is None:
                    continue
                same_scope = (
                    first["carrier_id"] == second["carrier_id"]
                    and first["zone"] == second["zone"]
                    and first["effective_from"] == second["effective_from"]
                )
                same_range = (
                    first["min_weight_kg"] == second["min_weight_kg"]
                    and first["max_weight_kg"] == second["max_weight_kg"]
                )
                overlaps = (
                    first["min_weight_kg"] < second["max_weight_kg"]
                    and second["min_weight_kg"] < first["max_weight_kg"]
                )
                if same_scope and overlaps and not same_range:
                    conflicts.setdefault(first_row["row_number"], []).append(
                        second_row["row_number"]
                    )
                    conflicts.setdefault(second_row["row_number"], []).append(
                        first_row["row_number"]
                    )

        for row in rows:
            conflicting_rows = conflicts.get(row["row_number"])
            if not conflicting_rows:
                continue
            references = ", ".join(str(number) for number in conflicting_rows)
            row["status"] = "rejected"
            row["reason"] = (
                f"El rango se traslapa con la fila {references} para la misma paquetería, "
                "zona y vigencia; requiere confirmación de Comercial."
            )
            row["normalized_data"] = None
            row["rate"] = None
