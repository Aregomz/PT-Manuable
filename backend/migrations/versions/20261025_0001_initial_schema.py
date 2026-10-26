"""Create the initial phase one schema.

Revision ID: 20261025_0001
Revises:
Create Date: 2026-10-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261025_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE carriers (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            code VARCHAR(32) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL UNIQUE,
            service_type VARCHAR(50) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT carriers_code_not_blank CHECK (btrim(code) <> ''),
            CONSTRAINT carriers_name_not_blank CHECK (btrim(name) <> '')
        );

        CREATE TABLE rate_imports (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            file_checksum CHAR(64) NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            total_rows INTEGER NOT NULL DEFAULT 0,
            loaded_rows INTEGER NOT NULL DEFAULT 0,
            corrected_rows INTEGER NOT NULL DEFAULT 0,
            rejected_rows INTEGER NOT NULL DEFAULT 0,
            duplicate_rows INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMPTZ,
            CONSTRAINT rate_imports_filename_not_blank CHECK (btrim(filename) <> ''),
            CONSTRAINT rate_imports_status_valid
                CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
            CONSTRAINT rate_imports_counts_nonnegative CHECK (
                total_rows >= 0
                AND loaded_rows >= 0
                AND corrected_rows >= 0
                AND rejected_rows >= 0
                AND duplicate_rows >= 0
            ),
            CONSTRAINT rate_imports_completed_at_valid CHECK (
                completed_at IS NULL OR completed_at >= started_at
            )
        );

        CREATE TABLE rate_import_rows (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            import_id BIGINT NOT NULL REFERENCES rate_imports(id) ON DELETE CASCADE,
            row_number INTEGER NOT NULL,
            raw_data JSONB NOT NULL,
            normalized_data JSONB,
            changes JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(20) NOT NULL,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT rate_import_rows_number_positive CHECK (row_number > 0),
            CONSTRAINT rate_import_rows_status_valid
                CHECK (status IN ('loaded', 'corrected', 'rejected', 'duplicate')),
            CONSTRAINT rate_import_rows_changes_array
                CHECK (jsonb_typeof(changes) = 'array'),
            CONSTRAINT rate_import_rows_rejection_reason CHECK (
                status <> 'rejected' OR reason IS NOT NULL
            ),
            CONSTRAINT rate_import_rows_import_row_unique UNIQUE (import_id, row_number)
        );

        CREATE TABLE rates (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            carrier_id BIGINT NOT NULL REFERENCES carriers(id) ON DELETE RESTRICT,
            zone SMALLINT NOT NULL,
            min_weight_kg NUMERIC(10, 3) NOT NULL,
            max_weight_kg NUMERIC(10, 3) NOT NULL,
            price_mxn NUMERIC(12, 2) NOT NULL,
            min_delivery_days SMALLINT,
            max_delivery_days SMALLINT,
            effective_from DATE,
            source_import_row_id BIGINT UNIQUE
                REFERENCES rate_import_rows(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT rates_zone_valid CHECK (zone BETWEEN 1 AND 4),
            CONSTRAINT rates_weight_range_valid CHECK (
                min_weight_kg >= 0 AND max_weight_kg > min_weight_kg
            ),
            CONSTRAINT rates_price_positive CHECK (price_mxn > 0),
            CONSTRAINT rates_delivery_days_valid CHECK (
                (min_delivery_days IS NULL AND max_delivery_days IS NULL)
                OR (
                    min_delivery_days > 0
                    AND max_delivery_days >= min_delivery_days
                )
            )
        );

        CREATE UNIQUE INDEX rates_business_key_unique
            ON rates (
                carrier_id,
                zone,
                min_weight_kg,
                max_weight_kg,
                COALESCE(effective_from, DATE '0001-01-01')
            );

        CREATE INDEX rates_lookup_idx
            ON rates (zone, min_weight_kg, max_weight_kg, carrier_id);

        CREATE INDEX rate_import_rows_import_status_idx
            ON rate_import_rows (import_id, status);

        CREATE TABLE leads (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email VARCHAR(254) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT leads_email_normalized CHECK (email = lower(btrim(email))),
            CONSTRAINT leads_email_not_blank CHECK (btrim(email) <> '')
        );

        CREATE TABLE quotes (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            lead_id BIGINT NOT NULL REFERENCES leads(id) ON DELETE RESTRICT,
            origin_postal_code VARCHAR(5) NOT NULL,
            destination_postal_code VARCHAR(5) NOT NULL,
            weight_kg NUMERIC(10, 3) NOT NULL,
            origin_latitude NUMERIC(9, 6) NOT NULL,
            origin_longitude NUMERIC(9, 6) NOT NULL,
            destination_latitude NUMERIC(9, 6) NOT NULL,
            destination_longitude NUMERIC(9, 6) NOT NULL,
            distance_km NUMERIC(10, 2) NOT NULL,
            zone SMALLINT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT quotes_origin_postal_code_valid
                CHECK (origin_postal_code ~ '^[0-9]{5}$'),
            CONSTRAINT quotes_destination_postal_code_valid
                CHECK (destination_postal_code ~ '^[0-9]{5}$'),
            CONSTRAINT quotes_weight_positive CHECK (weight_kg > 0),
            CONSTRAINT quotes_origin_latitude_valid
                CHECK (origin_latitude BETWEEN -90 AND 90),
            CONSTRAINT quotes_origin_longitude_valid
                CHECK (origin_longitude BETWEEN -180 AND 180),
            CONSTRAINT quotes_destination_latitude_valid
                CHECK (destination_latitude BETWEEN -90 AND 90),
            CONSTRAINT quotes_destination_longitude_valid
                CHECK (destination_longitude BETWEEN -180 AND 180),
            CONSTRAINT quotes_distance_nonnegative CHECK (distance_km >= 0),
            CONSTRAINT quotes_zone_valid CHECK (zone BETWEEN 1 AND 4)
        );

        CREATE INDEX quotes_lead_created_at_idx
            ON quotes (lead_id, created_at DESC);

        CREATE INDEX quotes_created_at_idx
            ON quotes (created_at DESC);

        CREATE TABLE quote_options (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            quote_id BIGINT NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
            carrier_id BIGINT NOT NULL REFERENCES carriers(id) ON DELETE RESTRICT,
            rate_id BIGINT REFERENCES rates(id) ON DELETE SET NULL,
            carrier_name VARCHAR(100) NOT NULL,
            price_mxn NUMERIC(12, 2) NOT NULL,
            min_delivery_days SMALLINT,
            max_delivery_days SMALLINT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT quote_options_carrier_name_not_blank
                CHECK (btrim(carrier_name) <> ''),
            CONSTRAINT quote_options_price_positive CHECK (price_mxn > 0),
            CONSTRAINT quote_options_delivery_days_valid CHECK (
                (min_delivery_days IS NULL AND max_delivery_days IS NULL)
                OR (
                    min_delivery_days > 0
                    AND max_delivery_days >= min_delivery_days
                )
            ),
            CONSTRAINT quote_options_quote_carrier_unique UNIQUE (quote_id, carrier_id)
        );

        CREATE TABLE postal_codes (
            postal_code VARCHAR(5) PRIMARY KEY,
            latitude NUMERIC(9, 6) NOT NULL,
            longitude NUMERIC(9, 6) NOT NULL,
            place_name VARCHAR(150),
            fetched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT postal_codes_format_valid
                CHECK (postal_code ~ '^[0-9]{5}$'),
            CONSTRAINT postal_codes_latitude_valid CHECK (latitude BETWEEN -90 AND 90),
            CONSTRAINT postal_codes_longitude_valid CHECK (longitude BETWEEN -180 AND 180)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS postal_codes;
        DROP TABLE IF EXISTS quote_options;
        DROP TABLE IF EXISTS quotes;
        DROP TABLE IF EXISTS leads;
        DROP TABLE IF EXISTS rates;
        DROP TABLE IF EXISTS rate_import_rows;
        DROP TABLE IF EXISTS rate_imports;
        DROP TABLE IF EXISTS carriers;
        """
    )
