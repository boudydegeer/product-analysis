"""flatten_analysis_result_structure

Revision ID: 6681421c3eb9
Revises: b1a75753608
Create Date: 2026-01-08 08:56:41.772677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6681421c3eb9"
down_revision: Union[str, Sequence[str], None] = "b1a75753608"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add flattened analysis columns."""
    # Add new flattened columns
    op.add_column("analyses", sa.Column("summary_overview", sa.Text(), nullable=True))
    op.add_column(
        "analyses",
        sa.Column(
            "summary_key_points", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "summary_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "implementation_architecture",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "implementation_technical_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "implementation_data_flow",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "risks_technical_risks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "risks_security_concerns",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "risks_scalability_issues",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "risks_mitigation_strategies",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "recommendations_improvements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "recommendations_best_practices",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "analyses",
        sa.Column(
            "recommendations_next_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove flattened analysis columns."""
    op.drop_column("analyses", "recommendations_next_steps")
    op.drop_column("analyses", "recommendations_best_practices")
    op.drop_column("analyses", "recommendations_improvements")
    op.drop_column("analyses", "risks_mitigation_strategies")
    op.drop_column("analyses", "risks_scalability_issues")
    op.drop_column("analyses", "risks_security_concerns")
    op.drop_column("analyses", "risks_technical_risks")
    op.drop_column("analyses", "implementation_data_flow")
    op.drop_column("analyses", "implementation_technical_details")
    op.drop_column("analyses", "implementation_architecture")
    op.drop_column("analyses", "summary_metrics")
    op.drop_column("analyses", "summary_key_points")
    op.drop_column("analyses", "summary_overview")
