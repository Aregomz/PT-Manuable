from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


class CatalogRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def list_carriers(self) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, code, name, service_type, is_active,
                       volumetric_divisor, volumetric_effective_from, updated_at
                FROM carriers
                ORDER BY name
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_rates(self) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    rates.id,
                    carriers.name AS carrier_name,
                    carriers.is_active AS carrier_is_active,
                    rates.zone,
                    rates.min_weight_kg,
                    rates.max_weight_kg,
                    rates.price_mxn,
                    rates.min_delivery_days,
                    rates.max_delivery_days,
                    rates.effective_from
                FROM rates
                JOIN carriers ON carriers.id = rates.carrier_id
                ORDER BY carriers.name, rates.zone, rates.min_weight_kg, rates.effective_from
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_carrier(
        self,
        carrier_id: int,
        *,
        name: str,
        service_type: str,
        is_active: bool,
        volumetric_divisor: Any,
        volumetric_effective_from: Any,
    ) -> dict[str, Any] | None:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                UPDATE carriers
                SET name = %s,
                    service_type = %s,
                    is_active = %s,
                    volumetric_divisor = %s,
                    volumetric_effective_from = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, code, name, service_type, is_active,
                          volumetric_divisor, volumetric_effective_from, updated_at
                """,
                (
                    name,
                    service_type,
                    is_active,
                    volumetric_divisor,
                    volumetric_effective_from,
                    carrier_id,
                ),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_rate(
        self,
        rate_id: int,
        *,
        zone: int,
        min_weight_kg: Any,
        max_weight_kg: Any,
        price_mxn: Any,
        min_delivery_days: int | None,
        max_delivery_days: int | None,
        effective_from: Any,
    ) -> dict[str, Any] | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE rates
                SET zone = %s,
                    min_weight_kg = %s,
                    max_weight_kg = %s,
                    price_mxn = %s,
                    min_delivery_days = %s,
                    max_delivery_days = %s,
                    effective_from = %s
                WHERE id = %s
                RETURNING id
                """,
                (
                    zone,
                    min_weight_kg,
                    max_weight_kg,
                    price_mxn,
                    min_delivery_days,
                    max_delivery_days,
                    effective_from,
                    rate_id,
                ),
            )
            if cursor.fetchone() is None:
                return None

        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    rates.id,
                    carriers.name AS carrier_name,
                    carriers.is_active AS carrier_is_active,
                    rates.zone,
                    rates.min_weight_kg,
                    rates.max_weight_kg,
                    rates.price_mxn,
                    rates.min_delivery_days,
                    rates.max_delivery_days,
                    rates.effective_from
                FROM rates
                JOIN carriers ON carriers.id = rates.carrier_id
                WHERE rates.id = %s
                """,
                (rate_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
