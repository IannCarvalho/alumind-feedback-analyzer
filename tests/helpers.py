"""Auxiliares de teste para formulários protegidos por CSRF."""
import re

_TOKEN_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


def csrf_token(client) -> str:
    """Token CSRF da sessão do client.

    O painel virou SPA, então a única página server-rendered com o campo é o
    ``/login`` (usado antes de logar). Depois do login o ``/login`` redireciona,
    então o token vem da API de settings — a mesma fonte que o SPA consome.
    """
    match = _TOKEN_RE.search(client.get("/login").get_data(as_text=True))
    if match:
        return match.group(1)
    data = client.get("/api/settings/providers").get_json(silent=True) or {}
    token = data.get("csrf_token")
    if token:
        return token
    raise AssertionError("nenhuma fonte de csrf_token (auth desligada?)")


def post_form(client, path, data=None, **kwargs):
    """POST de formulário com o token CSRF da sessão do client."""
    payload = {"csrf_token": csrf_token(client), **(data or {})}
    return client.post(path, data=payload, **kwargs)


def login(client, password, **kwargs):
    return post_form(client, "/login", {"password": password}, **kwargs)
