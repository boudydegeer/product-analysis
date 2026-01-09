"""add codebase_explorations table

Revision ID: 8dfc784b46c2
Revises: 637491144f95
Create Date: 2026-01-09 19:48:11.860767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8dfc784b46c2'
down_revision: Union[str, Sequence[str], None] = '637491144f95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('codebase_explorations',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('session_id', sa.String(length=50), nullable=True),
    sa.Column('message_id', sa.String(length=50), nullable=True),
    sa.Column('query', sa.Text(), nullable=False),
    sa.Column('scope', sa.String(length=20), nullable=False),
    sa.Column('focus', sa.String(length=20), nullable=False),
    sa.Column('workflow_run_id', sa.String(length=50), nullable=True),
    sa.Column('workflow_url', sa.String(length=500), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'INVESTIGATING', 'COMPLETED', 'FAILED', name='codebaseexplorationstatus'), nullable=False),
    sa.Column('results', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('formatted_context', sa.Text(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_codebase_explorations_session_id', 'codebase_explorations', ['session_id'], unique=False)
    op.create_index('idx_codebase_explorations_status', 'codebase_explorations', ['status'], unique=False)
    op.create_index('idx_codebase_explorations_workflow_run_id', 'codebase_explorations', ['workflow_run_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_codebase_explorations_workflow_run_id', table_name='codebase_explorations')
    op.drop_index('idx_codebase_explorations_status', table_name='codebase_explorations')
    op.drop_index('idx_codebase_explorations_session_id', table_name='codebase_explorations')
    op.drop_table('codebase_explorations')
    op.execute('DROP TYPE IF EXISTS codebaseexplorationstatus')
