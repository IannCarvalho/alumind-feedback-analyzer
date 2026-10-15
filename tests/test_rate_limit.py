"""Testes do rate-limiting no endpoint público de ingestão.

Os testes constroem um app com o limitador LIGADO e um limite propositalmente
baixo, isolando o storage em memória, para provar que o 429 dispara e que a
resposta é JSON (não o HTML default do Flask-Limiter).
"""
import os
from unittest.mock import patch

import pytest

from app import create_app, db
from app.config import Config


class RateLimitedConfig(Config):
    """Config de teste com rate-limit ligado e um limite baixo."""
    TESTING = True
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = 'memory://'
    RATELIMIT_INGEST = '2 per minute'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


@pytest.fixture()
def limited_client():
    """Client de um app com o rate-limit ativo (limite de 2/min)."""
    # Garante a key para o FeedbackAnalyzer construído no import do blueprint.
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')
    application = create_app(RateLimitedConfig)
    with application.app_context():
        db.create_all()
        # Reseta qualquer estado acumulado do storage em memória entre testes.
        from app.extensions import limiter
        limiter.reset()
        yield application.test_client()
        db.session.remove()
        db.drop_all()
        limiter.reset()


def _valid_payload(suffix: str):
    return {
        'id': f'00000000-0000-0000-0000-0000000000{suffix}',
        'feedback': 'Ótimo produto, só queria um modo escuro.',
    }


def test_ingest_within_limit_is_allowed(limited_client):
    """As primeiras requisições dentro do limite passam normalmente."""
    with patch(
        'app.routes.api.feedback_analyzer.analyze_feedback',
        return_value={
            'sentiment': 'POSITIVO',
            'is_spam': False,
            'requested_features': [],
        },
    ):
        r1 = limited_client.post('/api/feedbacks', json=_valid_payload('01'))
        r2 = limited_client.post('/api/feedbacks', json=_valid_payload('02'))

    assert r1.status_code == 201
    assert r2.status_code == 201


def test_ingest_over_limit_returns_429_json(limited_client):
    """A requisição acima do limite recebe 429 com corpo JSON."""
    with patch(
        'app.routes.api.feedback_analyzer.analyze_feedback',
        return_value={
            'sentiment': 'POSITIVO',
            'is_spam': False,
            'requested_features': [],
        },
    ):
        limited_client.post('/api/feedbacks', json=_valid_payload('01'))
        limited_client.post('/api/feedbacks', json=_valid_payload('02'))
        over = limited_client.post('/api/feedbacks', json=_valid_payload('03'))

    assert over.status_code == 429
    assert over.is_json
    body = over.get_json()
    assert body['error'] == 'Too many requests'


def test_get_endpoints_not_rate_limited(limited_client):
    """O GET de listagem não carrega o limite da ingestão."""
    for _ in range(5):
        resp = limited_client.get('/api/feedbacks')
        assert resp.status_code == 200
