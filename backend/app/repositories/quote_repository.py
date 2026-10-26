from datetime import date
from decimal import Decimal
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

from app.integrations.zippopotam import PostalLocation


class QuoteRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def find_postal_code(self, postal_code: str) -> dict[str, Any] | None:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM postal_codes WHERE postal_code = %s", (postal_code,))
            row = cursor.fetchone()
        return dict(row) if row else None

    def save_postal_code(self, location: PostalLocation) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO postal_codes (postal_code, latitude, longitude, place_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (postal_code) DO UPDATE SET
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    place_name = EXCLUDED.place_name,
                    fetched_at = CURRENT_TIMESTAMP
                """,
                (
                    location.postal_code,
                    location.latitude,
                    location.longitude,
                    location.place_name,
                ),
            )

    def find_rates(
        self,
        zone: int,
        weight_kg: Decimal,
        volumetric_weight_kg: Decimal | None,
        quote_date: date,
    ) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                WITH carrier_weights AS (
                    SELECT
                        carriers.*,
                        CASE
                            WHEN carriers.volumetric_effective_from IS NOT NULL
                                AND carriers.volumetric_effective_from <= %(quote_date)s
                                AND %(volumetric_weight_kg)s IS NULL
                            THEN NULL
                            WHEN carriers.volumetric_effective_from IS NOT NULL
                                AND carriers.volumetric_effective_from <= %(quote_date)s
                            THEN GREATEST(%(weight_kg)s, %(volumetric_weight_kg)s)
                            ELSE %(weight_kg)s
                        END AS billable_weight_kg
                    FROM carriers
                    WHERE carriers.is_active = TRUE
                )
                SELECT DISTINCT ON (carriers.id)
                    rates.id AS rate_id,
                    carriers.id AS carrier_id,
                    carriers.name AS carrier_name,
                    rates.price_mxn,
                    rates.min_delivery_days,
                    rates.max_delivery_days,
                    %(weight_kg)s AS actual_weight_kg,
                    %(volumetric_weight_kg)s AS volumetric_weight_kg,
                    carriers.billable_weight_kg
                FROM rates
                JOIN carrier_weights AS carriers ON carriers.id = rates.carrier_id
                WHERE carriers.billable_weight_kg IS NOT NULL
                  AND rates.zone = %(zone)s
                  AND rates.min_weight_kg <= carriers.billable_weight_kg
                  AND rates.max_weight_kg >= carriers.billable_weight_kg
                  AND (rates.effective_from IS NULL OR rates.effective_from <= %(quote_date)s)
                ORDER BY
                    carriers.id,
                    rates.min_weight_kg ASC,
                    rates.effective_from DESC NULLS LAST
                """,
                {
                    "zone": zone,
                    "weight_kg": weight_kg,
                    "volumetric_weight_kg": volumetric_weight_kg,
                    "quote_date": quote_date,
                },
            )
            rates = [dict(row) for row in cursor.fetchall()]
        return sorted(rates, key=lambda rate: rate["price_mxn"])

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
            raise RuntimeError("No fue posible guardar el lead.")
        return int(row[0])

    def create_quote(self, lead_id: int, quote: dict[str, Any]) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO quotes (
                    lead_id, external_reference, source,
                    origin_postal_code, destination_postal_code, weight_kg,
                    length_cm, width_cm, height_cm, volumetric_weight_kg,
                    origin_latitude, origin_longitude, destination_latitude,
                    destination_longitude, distance_km, zone, quoted_at, valid_until
                ) VALUES (
                    %(lead_id)s, %(external_reference)s, 'public',
                    %(origin_postal_code)s, %(destination_postal_code)s, %(weight_kg)s,
                    %(length_cm)s, %(width_cm)s, %(height_cm)s, %(volumetric_weight_kg)s,
                    %(origin_latitude)s, %(origin_longitude)s,
                    %(destination_latitude)s, %(destination_longitude)s,
                    %(distance_km)s, %(zone)s, %(quoted_at)s, %(valid_until)s
                ) RETURNING id
                """,
                {"lead_id": lead_id, **quote},
            )
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No fue posible guardar la cotización.")
        return int(row[0])

    def save_options(self, quote_id: int, rates: list[dict[str, Any]]) -> None:
        with self.connection.cursor() as cursor:
            for rate in rates:
                cursor.execute(
                    """
                    INSERT INTO quote_options (
                        quote_id, carrier_id, rate_id, carrier_name, price_mxn,
                        min_delivery_days, max_delivery_days, actual_weight_kg,
                        volumetric_weight_kg, billable_weight_kg
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        quote_id,
                        rate["carrier_id"],
                        rate["rate_id"],
                        rate["carrier_name"],
                        rate["price_mxn"],
                        rate["min_delivery_days"],
                        rate["max_delivery_days"],
                        rate["actual_weight_kg"],
                        rate["volumetric_weight_kg"],
                        rate["billable_weight_kg"],
                    ),
                )

