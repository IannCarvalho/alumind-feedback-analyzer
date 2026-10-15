"""Testes do CORS escopado às rotas da API."""


def test_cors_header_present_on_api(client):
    """Uma requisição com Origin a /api recebe o header CORS."""
    resp = client.get('/api/feedbacks', headers={'Origin': 'https://exemplo.com'})
    assert resp.status_code == 200
    assert 'Access-Control-Allow-Origin' in resp.headers


def test_cors_preflight_on_api(client):
    """O preflight OPTIONS em /api é respondido com os headers de CORS."""
    resp = client.options(
        '/api/feedbacks',
        headers={
            'Origin': 'https://exemplo.com',
            'Access-Control-Request-Method': 'POST',
        },
    )
    assert resp.status_code in (200, 204)
    assert 'Access-Control-Allow-Origin' in resp.headers


def test_no_cors_header_on_web_routes(client):
    """Rotas web (sessão de dashboard) não ganham header CORS."""
    resp = client.get('/health', headers={'Origin': 'https://exemplo.com'})
    # /health não está sob /api, então não deve carregar CORS.
    assert 'Access-Control-Allow-Origin' not in resp.headers
