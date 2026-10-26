from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row


class LeadRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def list_leads_with_quotes(self) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    leads.id AS lead_id,
                    leads.email,
                    leads.created_at AS lead_created_at,
                    quotes.id AS quote_id,
                    quotes.external_reference,
                    quotes.source,
                    quotes.origin_postal_code,
                    quotes.destination_postal_code,
                    quotes.weight_kg,
                    quotes.distance_km,
                    quotes.zone,
                    quotes.quoted_at,
                    quotes.valid_until,
                    COUNT(quote_options.id) AS option_count,
                    COALESCE(
                        jsonb_agg(
                            jsonb_build_object(
                                'carrier_name', quote_options.carrier_name,
                                'price_mxn', quote_options.price_mxn,
                                'min_delivery_days', quote_options.min_delivery_days,
                                'max_delivery_days', quote_options.max_delivery_days,
                                'billable_weight_kg', quote_options.billable_weight_kg
                            ) ORDER BY quote_options.price_mxn
                        ) FILTER (WHERE quote_options.id IS NOT NULL),
                        '[]'::jsonb
                    ) AS options
                FROM leads
                LEFT JOIN quotes ON quotes.lead_id = leads.id
                LEFT JOIN quote_options ON quote_options.quote_id = quotes.id
                GROUP BY leads.id, quotes.id
                ORDER BY leads.created_at DESC, quotes.quoted_at DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_daily_metrics(self) -> list[dict[str, Any]]:
        with self.connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    quotes.quoted_at::date AS date,
                    COUNT(*) AS total_quotes,
                    COUNT(*) FILTER (
                        WHERE NOT EXISTS (
                            SELECT 1 FROM quote_options
                            WHERE quote_options.quote_id = quotes.id
                        )
                    ) AS without_options
                FROM quotes
                GROUP BY quotes.quoted_at::date
                ORDER BY date DESC
                LIMIT 30
                """
            )
            return [dict(row) for row in cursor.fetchall()]

