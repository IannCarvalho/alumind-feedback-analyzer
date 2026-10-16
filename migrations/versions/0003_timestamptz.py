"""created_at passa a TIMESTAMP WITH TIME ZONE.

O app sempre gravou ``datetime.now(timezone.utc)``, mas a coluna era
``TIMESTAMP WITHOUT TIME ZONE``: o Postgres descartava o fuso e a leitura
voltava ingênua. Os valores existentes já estão em UTC, então a conversão é
``AT TIME ZONE 'UTC'`` (sem deslocar nenhuma linha). No SQLite (testes) não
há tipo com fuso e a revisão não muda nada.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

_COLUMNS = (('feedbacks', 'created_at'), ('requested_features', 'created_at'))


def _is_postgres():
    return op.get_bind().dialect.name == 'postgresql'


def upgrade():
    if not _is_postgres():
        return
    for table, column in _COLUMNS:
        op.alter_column(
            table, column,
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade():
    if not _is_postgres():
        return
    for table, column in _COLUMNS:
        op.alter_column(
            table, column,
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
