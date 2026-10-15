"""Testes do endpoint de health check."""
from unittest.mock import patch


def test_health_ok(client):
    """Com o banco acessível, /health responde 200 e status ok."""
    resp = client.get('/health')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['status'] == 'ok'
    assert body['database'] == 'ok'


def test_health_degraded_on_db_error(client):
    """Se o SELECT 1 falha, /health responde 503 e status degraded."""
    with patch('app.routes.health.db.session.execute',
               side_effect=Exception('db down')):
        resp = client.get('/health')
    assert resp.status_code == 503
    body = resp.get_json()
    assert body['status'] == 'degraded'
    assert body['database'] == 'error'


def test_health_not_behind_auth(client):
    """O probe funciona mesmo com autenticação ligada."""
    client.application.config['DASHBOARD_PASSWORD'] = 'segredo'
    resp = client.get('/health')
    assert resp.status_code == 200
