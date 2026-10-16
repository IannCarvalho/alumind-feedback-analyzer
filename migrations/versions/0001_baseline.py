"""Baseline: tabelas feedbacks e requested_features.

Reproduz o esquema que o app tinha antes das migrations versionadas
(timestamps sem fuso e sem índices); os ajustes vêm nas revisões seguintes.
Bancos que já foram criados por ``flask db migrate`` ou ``db.create_all()``
devem rodar ``flask db stamp 0001`` e depois ``flask db upgrade``.

Revision ID: 0001
Revises:
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

from app.models.types import GUID

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feedbacks',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=False),
        sa.Column('sentiment', sa.String(length=20), nullable=True),
        sa.Column('is_spam', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'requested_features',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('feedback_id', GUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['feedback_id'], ['feedbacks.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('requested_features')
    op.drop_table('feedbacks')
