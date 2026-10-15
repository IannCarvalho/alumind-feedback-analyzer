"""Shared pytest fixtures and environment setup.

A dummy OPENAI_API_KEY is set before any app import because FeedbackAnalyzer
validates the key at construction time and the api blueprint builds one at
import time. With the dialect-agnostic GUID column type, the models now run on
in-memory SQLite, so DB-backed integration tests are possible.
"""
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")
# Desliga o rate-limit nos testes: o limitador é configurado no init_app a
# partir do config (lido do ambiente), então precisa estar definido aqui,
# antes de qualquer import do app, e não após create_app().
os.environ.setdefault("RATELIMIT_ENABLED", "false")

import pytest

from app import create_app, db


@pytest.fixture()
def app():
    """A Flask app bound to an in-memory SQLite database with tables created."""
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()
