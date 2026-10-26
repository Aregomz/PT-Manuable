"""Add phase two quoting and historical import fields.

Revision ID: 20261120_0002
Revises: 20261025_0001
Create Date: 2026-11-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261120_0002"
down_revision: str | None = "20261025_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE carriers
            ADD COLUMN volumetric_divisor NUMERIC(10, 2),
            ADD COLUMN volumetric_effective_from DATE,
            ADD CONSTRAINT carriers_volumetric_configuration_valid CHECK (
                (volumetric_divisor IS NULL AND volumetric_effective_from IS NULL)
                OR (volumetric_divisor > 0 AND volumetric_effective_from IS NOT NULL)
            );

        UPDATE carriers
        SET volumetric_divisor = 5000,
            volumetric_effective_from = DATE '2026-12-01',
            updated_at = CURRENT_TIMESTAMP
        WHERE lower(name) IN ('dhl', 'fedex');

        ALTER TABLE quotes
            ADD COLUMN external_reference VARCHAR(50) UNIQUE,
            ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'public',
            ADD COLUMN length_cm NUMERIC(10, 2),
            ADD COLUMN width_cm NUMERIC(10, 2),
            ADD COLUMN height_cm NUMERIC(10, 2),
            ADD COLUMN volumetric_weight_kg NUMERIC(10, 3),
            ADD COLUMN quoted_at TIMESTAMPTZ,
            ADD COLUMN valid_until TIMESTAMPTZ,
            ADD COLUMN source_import_row_id BIGINT UNIQUE
                REFERENCES rate_import_rows(id) ON DELETE SET NULL;

        UPDATE quotes
        SET external_reference = 'WEB-' || lpad(id::text, 8, '0'),
            quoted_at = created_at,
            valid_until = created_at + INTERVAL '30 days';

        ALTER TABLE quotes
            ALTER COLUMN external_reference SET NOT NULL,
            ALTER COLUMN quoted_at SET NOT NULL,
            ALTER COLUMN valid_until SET NOT NULL,
            ALTER COLUMN origin_latitude DROP NOT NULL,
            ALTER COLUMN origin_longitude DROP NOT NULL,
            ALTER COLUMN destination_latitude DROP NOT NULL,
            ALTER COLUMN destination_longitude DROP NOT NULL,
            ALTER COLUMN distance_km DROP NOT NULL,
            ADD CONSTRAINT quotes_source_valid CHECK (source IN ('public', 'historical')),
            ADD CONSTRAINT quotes_dimensions_valid CHECK (
                (length_cm IS NULL AND width_cm IS NULL AND height_cm IS NULL)
                OR (length_cm > 0 AND width_cm > 0 AND height_cm > 0)
            ),
            ADD CONSTRAINT quotes_volumetric_weight_valid CHECK (
                volumetric_weight_kg IS NULL OR volumetric_weight_kg > 0
            ),
            ADD CONSTRAINT quotes_validity_valid CHECK (
                valid_until = quoted_at + INTERVAL '30 days'
            );

        ALTER TABLE quote_options
            ADD COLUMN actual_weight_kg NUMERIC(10, 3),
            ADD COLUMN volumetric_weight_kg NUMERIC(10, 3),
            ADD COLUMN billable_weight_kg NUMERIC(10, 3);

        UPDATE quote_options AS qo
        SET actual_weight_kg = q.weight_kg,
            billable_weight_kg = q.weight_kg
        FROM quotes AS q
        WHERE q.id = qo.quote_id;

        ALTER TABLE quote_options
            ALTER COLUMN actual_weight_kg SET NOT NULL,
            ALTER COLUMN billable_weight_kg SET NOT NULL,
            ADD CONSTRAINT quote_options_weights_valid CHECK (
                actual_weight_kg > 0
                AND billable_weight_kg > 0
                AND (volumetric_weight_kg IS NULL OR volumetric_weight_kg > 0)
            );

        CREATE INDEX quotes_quoted_at_idx ON quotes (quoted_at DESC);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS quotes_quoted_at_idx;

        ALTER TABLE quote_options
            DROP CONSTRAINT IF EXISTS quote_options_weights_valid,
            DROP COLUMN IF EXISTS billable_weight_kg,
            DROP COLUMN IF EXISTS volumetric_weight_kg,
            DROP COLUMN IF EXISTS actual_weight_kg;

        DELETE FROM quotes WHERE source = 'historical';

        ALTER TABLE quotes
            DROP CONSTRAINT IF EXISTS quotes_validity_valid,
            DROP CONSTRAINT IF EXISTS quotes_volumetric_weight_valid,
            DROP CONSTRAINT IF EXISTS quotes_dimensions_valid,
            DROP CONSTRAINT IF EXISTS quotes_source_valid,
            ALTER COLUMN origin_latitude SET NOT NULL,
            ALTER COLUMN origin_longitude SET NOT NULL,
            ALTER COLUMN destination_latitude SET NOT NULL,
            ALTER COLUMN destination_longitude SET NOT NULL,
            ALTER COLUMN distance_km SET NOT NULL,
            DROP COLUMN IF EXISTS source_import_row_id,
            DROP COLUMN IF EXISTS valid_until,
            DROP COLUMN IF EXISTS quoted_at,
            DROP COLUMN IF EXISTS volumetric_weight_kg,
            DROP COLUMN IF EXISTS height_cm,
            DROP COLUMN IF EXISTS width_cm,
            DROP COLUMN IF EXISTS length_cm,
            DROP COLUMN IF EXISTS source,
            DROP COLUMN IF EXISTS external_reference;

        ALTER TABLE carriers
            DROP CONSTRAINT IF EXISTS carriers_volumetric_configuration_valid,
            DROP COLUMN IF EXISTS volumetric_effective_from,
            DROP COLUMN IF EXISTS volumetric_divisor;
        """
    )
