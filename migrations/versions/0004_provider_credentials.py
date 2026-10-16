"""Tabela provider_credentials: chaves de provedor cifradas, com prioridade.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

from app.models.types import GUID

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'provider_credentials',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('key_hint', sa.String(length=16), nullable=False),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error_kind', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'model',
                            name='uq_provider_credentials_provider_model'),
    )
    op.create_index('ix_provider_credentials_priority', 'provider_credentials',
                    ['priority'])


def downgrade():
    op.drop_index('ix_provider_credentials_priority',
                  table_name='provider_credentials')
    op.drop_table('provider_credentials')
