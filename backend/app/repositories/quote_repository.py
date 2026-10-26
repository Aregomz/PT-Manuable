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

    def find_rates(self, zone: int, weight_kg: Decimal) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT DISTINCT ON (carriers.id)
                    rates.id AS rate_id,
                    carriers.id AS carrier_id,
                    carriers.name AS carrier_name,
                    rates.price_mxn,
                    rates.min_delivery_days,
                    rates.max_delivery_days
                FROM rates
                JOIN carriers ON carriers.id = rates.carrier_id
                WHERE carriers.is_active = TRUE
                  AND rates.zone = %s
                  AND rates.min_weight_kg <= %s
                  AND rates.max_weight_kg >= %s
                  AND (rates.effective_from IS NULL OR rates.effective_from <= %s)
                ORDER BY
                    carriers.id,
                    rates.min_weight_kg ASC,
                    rates.effective_from DESC NULLS LAST
                """,
                (zone, weight_kg, weight_kg, date.today()),
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
                    lead_id, origin_postal_code, destination_postal_code, weight_kg,
                    origin_latitude, origin_longitude, destination_latitude,
                    destination_longitude, distance_km, zone
                ) VALUES (
                    %(lead_id)s, %(origin_postal_code)s, %(destination_postal_code)s,
                    %(weight_kg)s, %(origin_latitude)s, %(origin_longitude)s,
                    %(destination_latitude)s, %(destination_longitude)s,
                    %(distance_km)s, %(zone)s
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
                        min_delivery_days, max_delivery_days
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        quote_id,
                        rate["carrier_id"],
                        rate["rate_id"],
                        rate["carrier_name"],
                        rate["price_mxn"],
                        rate["min_delivery_days"],
                        rate["max_delivery_days"],
                    ),
                )

