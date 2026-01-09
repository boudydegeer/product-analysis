"""migrate brainstorm_messages content to jsonb

Revision ID: 164168489f7c
Revises: 3edb4986d634
Create Date: 2026-01-09 12:52:48.795016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '164168489f7c'
down_revision: Union[str, Sequence[str], None] = '3edb4986d634'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop existing messages (acceptable in dev)
    op.execute('TRUNCATE TABLE brainstorm_messages CASCADE')

    # Change column type from TEXT to JSONB
    op.alter_column(
        'brainstorm_messages',
        'content',
        type_=postgresql.JSONB,
        postgresql_using='content::jsonb'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Change back to TEXT
    op.alter_column(
        'brainstorm_messages',
        'content',
        type_=sa.Text,
        postgresql_using='content::text'
    )
