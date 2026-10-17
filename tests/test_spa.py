"""Testes do blueprint que serve o front Vue (app/routes/spa.py).

O SPA é o painel padrão, servido na raiz ``/`` e nos deep-links do Vue Router
(ex.: ``/providers``, ``/feedbacks/<id>``). Sem o build do Vite
(``<static>/spa/index.html``) a raiz responde 503 com uma mensagem clara (e
não 404, que confundiria com rota inexistente).

Os testes isolam a pasta estática em ``tmp_path`` para nunca tocar o build
real do repositório (e evitar o file-lock de ``send_from_directory`` no
Windows ao remover o arquivo depois).
"""


def test_spa_503_when_not_built(client, app, tmp_path):
    """Sem o build do front, a raiz responde 503 explicando como gerar."""
    app.static_folder = str(tmp_path)  # pasta vazia: nenhum spa/index.html
    resp = client.get('/')
    assert resp.status_code == 503
    assert b'front' in resp.data.lower() or b'vite' in resp.data.lower()


def test_spa_serves_index_at_root_and_deeplinks(client, app, tmp_path):
    """Com o index do build presente, a raiz e os deep-links entregam o SPA."""
    app.static_folder = str(tmp_path)
    spa_dir = tmp_path / 'spa'
    spa_dir.mkdir()
    (spa_dir / 'index.html').write_text(
        '<!doctype html><title>FeedLens SPA</title>', encoding='utf-8')

    for path in ('/', '/providers', '/feedbacks/abc-123'):
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert b'FeedLens SPA' in resp.data, path


def test_spa_catch_all_does_not_swallow_reserved_paths(client, app, tmp_path):
    """Caminhos reservados (API, health) nunca recebem o index do SPA."""
    app.static_folder = str(tmp_path)
    spa_dir = tmp_path / 'spa'
    spa_dir.mkdir()
    (spa_dir / 'index.html').write_text(
        '<!doctype html><title>FeedLens SPA</title>', encoding='utf-8')

    # /health tem rota própria: responde o health, não o index.
    assert client.get('/health').status_code == 200
    assert b'FeedLens SPA' not in client.get('/health').data


def test_spa_behind_login(client, app, tmp_path):
    """Com DASHBOARD_PASSWORD definido, a raiz exige login (redireciona)."""
    app.static_folder = str(tmp_path)
    app.config['DASHBOARD_PASSWORD'] = 'segredo-de-teste'
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert '/login' in resp.headers['Location']
