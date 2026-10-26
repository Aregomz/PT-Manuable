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
                    quotes.origin_postal_code,
                    quotes.destination_postal_code,
                    quotes.weight_kg,
                    quotes.distance_km,
                    quotes.zone,
                    quotes.created_at AS quote_created_at,
                    COUNT(quote_options.id) AS option_count
                FROM leads
                LEFT JOIN quotes ON quotes.lead_id = leads.id
                LEFT JOIN quote_options ON quote_options.quote_id = quotes.id
                GROUP BY leads.id, quotes.id
                ORDER BY leads.created_at DESC, quotes.created_at DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]

