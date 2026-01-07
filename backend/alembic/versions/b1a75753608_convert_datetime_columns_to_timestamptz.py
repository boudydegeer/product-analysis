"""convert datetime columns to timestamptz

Revision ID: b1a75753608
Revises: 03bcf4cf0146
Create Date: 2026-01-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a75753608'
down_revision: Union[str, Sequence[str], None] = '03bcf4cf0146'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - convert TIMESTAMP to TIMESTAMPTZ."""
    # Convert all datetime columns to TIMESTAMP WITH TIME ZONE
    # This ensures proper timezone handling for all datetime fields

    # Features table columns
    op.execute('ALTER TABLE features ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE features ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE features ALTER COLUMN webhook_received_at TYPE TIMESTAMP WITH TIME ZONE USING webhook_received_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE features ALTER COLUMN last_polled_at TYPE TIMESTAMP WITH TIME ZONE USING last_polled_at AT TIME ZONE \'UTC\'')

    # Analyses table columns (if exists)
    op.execute('ALTER TABLE analyses ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE analyses ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE \'UTC\'')
    op.execute('ALTER TABLE analyses ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE USING completed_at AT TIME ZONE \'UTC\'')


def downgrade() -> None:
    """Downgrade schema - convert TIMESTAMPTZ back to TIMESTAMP."""
    # Convert all datetime columns back to TIMESTAMP WITHOUT TIME ZONE
    # Note: This will strip timezone information

    # Features table columns
    op.execute('ALTER TABLE features ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE features ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE features ALTER COLUMN webhook_received_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE features ALTER COLUMN last_polled_at TYPE TIMESTAMP WITHOUT TIME ZONE')

    # Analyses table columns
    op.execute('ALTER TABLE analyses ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE analyses ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE analyses ALTER COLUMN completed_at TYPE TIMESTAMP WITHOUT TIME ZONE')
