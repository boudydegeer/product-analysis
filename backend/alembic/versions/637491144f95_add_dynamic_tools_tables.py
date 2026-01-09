"""add dynamic tools tables

Revision ID: 637491144f95
Revises: 164168489f7c
Create Date: 2026-01-09 16:59:04.436526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '637491144f95'
down_revision: Union[str, Sequence[str], None] = '164168489f7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tools table
    op.create_table(
        'tools',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('tool_type', sa.String(50), nullable=False),
        sa.Column('definition', JSONB, nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('is_dangerous', sa.Boolean(), default=False),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('version', sa.String(20), default='1.0.0'),
        sa.Column('tags', JSONB, default='[]'),
        sa.Column('example_usage', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
    )
    op.create_index('idx_tools_category', 'tools', ['category'])
    op.create_index('idx_tools_enabled', 'tools', ['enabled'])

    # Agent types table
    op.create_table(
        'agent_types',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('avatar_color', sa.String(7), default='#6366f1'),
        sa.Column('personality_traits', JSONB, default='[]'),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('streaming_enabled', sa.Boolean(), default=True),
        sa.Column('max_context_tokens', sa.Integer(), default=200000),
        sa.Column('temperature', sa.Float(), default=0.7),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('version', sa.String(20), default='1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_agent_types_enabled', 'agent_types', ['enabled'])

    # Agent tool configs (junction table)
    op.create_table(
        'agent_tool_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('agent_type_id', sa.Integer(), sa.ForeignKey('agent_types.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_id', sa.Integer(), sa.ForeignKey('tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enabled_for_agent', sa.Boolean(), default=True),
        sa.Column('order_index', sa.Integer()),
        sa.Column('allow_use', sa.Boolean(), default=True),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('usage_limit', sa.Integer()),
        sa.Column('allowed_parameters', JSONB),
        sa.Column('denied_parameters', JSONB),
        sa.Column('parameter_defaults', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_unique_constraint('uq_agent_tool', 'agent_tool_configs', ['agent_type_id', 'tool_id'])
    op.create_index('idx_agent_tool_configs_agent', 'agent_tool_configs', ['agent_type_id'])
    op.create_index('idx_agent_tool_configs_enabled', 'agent_tool_configs', ['enabled_for_agent'])

    # Tool usage audit
    op.create_table(
        'tool_usage_audit',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('session_id', sa.String(50)),
        sa.Column('agent_type_id', sa.Integer(), sa.ForeignKey('agent_types.id'), nullable=True),
        sa.Column('tool_id', sa.Integer(), sa.ForeignKey('tools.id'), nullable=True),
        sa.Column('parameters', JSONB),
        sa.Column('result', JSONB),
        sa.Column('status', sa.String(50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('execution_time_ms', sa.Integer()),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_id', sa.String(255)),
    )
    op.create_index('idx_audit_session', 'tool_usage_audit', ['session_id'])
    op.create_index('idx_audit_created', 'tool_usage_audit', ['created_at'])


def downgrade() -> None:
    op.drop_table('tool_usage_audit')
    op.drop_table('agent_tool_configs')
    op.drop_table('agent_types')
    op.drop_table('tools')
