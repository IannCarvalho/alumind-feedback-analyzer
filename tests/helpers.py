"""Auxiliares de teste para o login do painel (JSON + CSRF)."""
from urllib.parse import urlencode

CSRF_HEADER = "X-CSRF-Token"


def csrf_token(client) -> str:
    """Token CSRF da sessão do client, como o SPA o obtém (``GET /auth/session``).

    Não depende do build do front: o CI dos testes Python não compila o SPA.
    """
    return client.get("/auth/session").get_json()["csrf_token"]


def post_form(client, path, data=None, **kwargs):
    """POST de formulário com o token CSRF da sessão do client."""
    payload = {"csrf_token": csrf_token(client), **(data or {})}
    return client.post(path, data=payload, **kwargs)


def login(client, password, next_url=None, token=None, **kwargs):
    """``POST /login`` como o SPA faz: JSON + header ``X-CSRF-Token``.

    ``token`` sobrescreve o token da sessão (testes de CSRF); ``next_url``
    vai na query string, como a tela de login repassa.
    """
    path = "/login" if next_url is None else f"/login?{urlencode({'next': next_url})}"
    headers = {
        CSRF_HEADER: csrf_token(client) if token is None else token,
        **kwargs.pop("headers", {}),
    }
    return client.post(path, json={"password": password}, headers=headers, **kwargs)
