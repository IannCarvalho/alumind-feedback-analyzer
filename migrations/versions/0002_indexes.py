"""Índices para as consultas do painel, da API e do resumo semanal.

- feedbacks.created_at: ordenação da listagem e filtro do resumo semanal;
- feedbacks.is_spam: quase toda consulta filtra ``is_spam = false``;
- requested_features.feedback_id: o Postgres não indexa FK sozinho (JOINs e
  o ``IN`` do carregamento das features da listagem);
- requested_features.code: agrupamento do ranking de funcionalidades.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-16
"""
from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_feedbacks_created_at', 'feedbacks', ['created_at'])
    op.create_index('ix_feedbacks_is_spam', 'feedbacks', ['is_spam'])
    op.create_index('ix_requested_features_feedback_id',
                    'requested_features', ['feedback_id'])
    op.create_index('ix_requested_features_code', 'requested_features', ['code'])


def downgrade():
    op.drop_index('ix_requested_features_code', table_name='requested_features')
    op.drop_index('ix_requested_features_feedback_id',
                  table_name='requested_features')
    op.drop_index('ix_feedbacks_is_spam', table_name='feedbacks')
    op.drop_index('ix_feedbacks_created_at', table_name='feedbacks')
