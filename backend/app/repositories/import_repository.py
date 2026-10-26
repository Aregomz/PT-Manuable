import json
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


class ImportRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def find_by_checksum(self, checksum: str) -> dict[str, Any] | None:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM rate_imports WHERE file_checksum = %s", (checksum,))
            result = cursor.fetchone()
        return dict(result) if result else None

    def create_import(self, filename: str, checksum: str, total_rows: int) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rate_imports (filename, file_checksum, status, total_rows)
                VALUES (%s, %s, 'processing', %s)
                RETURNING id
                """,
                (filename, checksum, total_rows),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No fue posible crear el registro de importación.")
        return int(row[0])

    def upsert_carrier(self, carrier: dict[str, Any]) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO carriers (code, name, service_type, is_active)
                VALUES (%(code)s, %(name)s, %(service_type)s, %(is_active)s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    service_type = EXCLUDED.service_type,
                    is_active = EXCLUDED.is_active,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                carrier,
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No fue posible guardar la paquetería.")
        return int(row[0])

    def get_carriers(self) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT id, name FROM carriers")
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def upsert_lead(self, email: str) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO leads (email) VALUES (%s)
                ON CONFLICT (email) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (email,),
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No fue posible guardar el lead histórico.")
        return int(row[0])

    def add_historical_quote(self, import_row_id: int, quote: dict[str, Any]) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO quotes (
                    lead_id, external_reference, source, origin_postal_code,
                    destination_postal_code, weight_kg, zone, quoted_at, valid_until,
                    source_import_row_id
                ) VALUES (
                    %(lead_id)s, %(external_reference)s, 'historical', %(origin_postal_code)s,
                    %(destination_postal_code)s, %(weight_kg)s, %(zone)s, %(quoted_at)s,
                    %(valid_until)s, %(source_import_row_id)s
                )
                ON CONFLICT (external_reference) DO NOTHING
                RETURNING id
                """,
                {**quote, "source_import_row_id": import_row_id},
            )
            row = cursor.fetchone()
            if row is None:
                return False
            quote_id = int(row[0])
            cursor.execute(
                """
                INSERT INTO quote_options (
                    quote_id, carrier_id, carrier_name, price_mxn,
                    actual_weight_kg, billable_weight_kg
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    quote_id,
                    quote["carrier_id"],
                    quote["carrier_name"],
                    quote["price_mxn"],
                    quote["weight_kg"],
                    quote["weight_kg"],
                ),
            )
            return True

    def add_import_row(self, import_id: int, row: dict[str, Any]) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rate_import_rows (
                    import_id, row_number, raw_data, normalized_data, changes, status, reason
                ) VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                RETURNING id
                """,
                (
                    import_id,
                    row["row_number"],
                    json.dumps(row["raw_data"], ensure_ascii=False),
                    json.dumps(row["normalized_data"], ensure_ascii=False, default=str)
                    if row["normalized_data"] is not None
                    else None,
                    json.dumps(row["changes"], ensure_ascii=False),
                    row["status"],
                    row["reason"],
                ),
            )
            result = cursor.fetchone()
        if result is None:
            raise RuntimeError("No fue posible guardar la fila de importación.")
        return int(result[0])

    def add_rate(self, import_row_id: int, rate: dict[str, Any]) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rates (
                    carrier_id, zone, min_weight_kg, max_weight_kg, price_mxn,
                    min_delivery_days, max_delivery_days, effective_from, source_import_row_id
                ) VALUES (
                    %(carrier_id)s, %(zone)s, %(min_weight_kg)s, %(max_weight_kg)s,
                    %(price_mxn)s, %(min_delivery_days)s, %(max_delivery_days)s,
                    %(effective_from)s, %(source_import_row_id)s
                )
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                {**rate, "source_import_row_id": import_row_id},
            )
            return cursor.fetchone() is not None

    def update_row_status(self, row_id: int, status: str, reason: str | None = None) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                "UPDATE rate_import_rows SET status = %s, reason = %s WHERE id = %s",
                (status, reason, row_id),
            )

    def complete_import(self, import_id: int, counts: dict[str, int]) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE rate_imports SET
                    status = 'completed',
                    loaded_rows = %(loaded)s,
                    corrected_rows = %(corrected)s,
                    rejected_rows = %(rejected)s,
                    duplicate_rows = %(duplicate)s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %(import_id)s
                """,
                {**counts, "import_id": import_id},
            )

    def get_import(self, import_id: int) -> dict[str, Any]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT *, started_at AS created_at FROM rate_imports WHERE id = %s",
                (import_id,),
            )
            summary = cursor.fetchone()
            cursor.execute(
                """
                SELECT row_number, status, raw_data, normalized_data, changes, reason
                FROM rate_import_rows
                WHERE import_id = %s
                ORDER BY row_number
                """,
                (import_id,),
            )
            rows = cursor.fetchall()
        if summary is None:
            raise LookupError("Importación no encontrada.")
        return {**dict(summary), "rows": [dict(row) for row in rows]}
