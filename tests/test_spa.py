"""Testes do blueprint que serve o front Vue (app/routes/spa.py).

A rota ``/app`` é aditiva: só deve existir quando o build do Vite foi gerado
em ``<static>/spa/index.html``. Sem o build, responde 503 com uma mensagem
clara (e não 404, que confundiria com rota inexistente).

Os testes isolam a pasta estática em ``tmp_path`` para nunca tocar o build
real do repositório (e evitar o file-lock de ``send_from_directory`` no
Windows ao remover o arquivo depois).
"""


def test_spa_503_when_not_built(client, app, tmp_path):
    """Sem o build do front, /app responde 503 explicando como gerar."""
    app.static_folder = str(tmp_path)  # pasta vazia: nenhum spa/index.html
    resp = client.get('/app')
    assert resp.status_code == 503
    assert b'front' in resp.data.lower() or b'vite' in resp.data.lower()


def test_spa_serves_index_when_built(client, app, tmp_path):
    """Com o index do build presente, /app e as sub-rotas entregam o SPA."""
    app.static_folder = str(tmp_path)
    spa_dir = tmp_path / 'spa'
    spa_dir.mkdir()
    (spa_dir / 'index.html').write_text(
        '<!doctype html><title>FeedLens SPA</title>', encoding='utf-8')

    for path in ('/app', '/app/', '/app/providers'):
        resp = client.get(path)
        assert resp.status_code == 200, path
        assert b'FeedLens SPA' in resp.data, path


def test_spa_behind_login(client, app, tmp_path):
    """Com DASHBOARD_PASSWORD definido, /app exige login (redireciona)."""
    app.static_folder = str(tmp_path)
    app.config['DASHBOARD_PASSWORD'] = 'segredo-de-teste'
    resp = client.get('/app', follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert '/login' in resp.headers['Location']
