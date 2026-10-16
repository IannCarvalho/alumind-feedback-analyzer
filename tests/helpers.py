"""Auxiliares de teste para formulários protegidos por CSRF."""
import re

_TOKEN_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


def csrf_token(client) -> str:
    """Lê o token da sessão do client numa página que o renderiza."""
    for path in ("/login", "/dashboard"):
        match = _TOKEN_RE.search(client.get(path).get_data(as_text=True))
        if match:
            return match.group(1)
    raise AssertionError("nenhuma página com csrf_token (auth desligada?)")


def post_form(client, path, data=None, **kwargs):
    """POST de formulário com o token CSRF da sessão do client."""
    payload = {"csrf_token": csrf_token(client), **(data or {})}
    return client.post(path, data=payload, **kwargs)


def login(client, password, **kwargs):
    return post_form(client, "/login", {"password": password}, **kwargs)
