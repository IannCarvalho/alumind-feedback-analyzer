"""As migrations versionadas têm que reproduzir exatamente os modelos.

Sem isso, o esquema do ``create_all`` (testes) e o das migrations (produção)
divergem em silêncio. Os testes rodam num SQLite em arquivo; no CI o mesmo
caminho roda também contra um Postgres de verdade (ver ``ci.yml``).
"""
import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text

from app import create_app, db
from app.config import Config


@pytest.fixture()
def migrated_app(tmp_path):
    class FileDbConfig(Config):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'migrations.db'}"

    application = create_app(FileDbConfig)
    application.config.update(TESTING=True)
    with application.app_context():
        yield application
        db.session.remove()
        db.engine.dispose()


def test_upgrade_head_matches_models(migrated_app):
    upgrade()
    with db.engine.connect() as connection:
        context = MigrationContext.configure(connection)
        assert compare_metadata(context, db.metadata) == []


def test_indexes_are_created(migrated_app):
    upgrade()
    inspector = inspect(db.engine)
    feedback_indexes = {i["name"] for i in inspector.get_indexes("feedbacks")}
    feature_indexes = {
        i["name"] for i in inspector.get_indexes("requested_features")}
    assert {"ix_feedbacks_created_at", "ix_feedbacks_is_spam"} <= feedback_indexes
    assert {
        "ix_requested_features_feedback_id",
        "ix_requested_features_code",
    } <= feature_indexes


def test_downgrade_to_base_and_back(migrated_app):
    upgrade()
    downgrade(revision="base")
    assert set(inspect(db.engine).get_table_names()) <= {"alembic_version"}
    upgrade()
    assert {"feedbacks", "requested_features"} <= set(
        inspect(db.engine).get_table_names())


def test_existing_rows_survive_upgrade(migrated_app):
    """Um banco já em produção (baseline) recebe índices sem perder dados."""
    upgrade(revision="0001")
    with db.engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO feedbacks (id, feedback_text, is_spam, created_at) "
            "VALUES ('11111111-1111-1111-1111-111111111111', 'antigo', 0, "
            "'2026-01-02 03:04:05')"))
    upgrade()
    with db.engine.connect() as connection:
        rows = connection.execute(
            text("SELECT feedback_text FROM feedbacks")).all()
    assert rows == [("antigo",)]
