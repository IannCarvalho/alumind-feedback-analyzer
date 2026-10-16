"""Proteção CSRF do painel e da API de configuração.

Cookie de sessão com ``SameSite=Lax`` já barra a maioria dos ataques, mas não
todos (subdomínios irmãos, navegadores antigos, ``Lax`` com GET que muda
estado). Aqui há uma segunda camada, sem dependência extra: um token aleatório
POR SESSÃO, comparado em tempo constante com o que a requisição envia.

- Formulários HTML: ``<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">``.
- Chamadas JSON (``fetch``): header ``X-CSRF-Token``.

Vale para métodos que alteram estado (qualquer um fora de GET/HEAD/OPTIONS).
O token existe ANTES do login, o que protege também o próprio ``POST /login``
(login CSRF: forçar a vítima a entrar na conta do atacante) e é trocado
quando o login acontece (veja ``rotate_csrf_token``).
"""
import hmac
import secrets
from functools import wraps

from flask import Flask, abort, request, session

CSRF_SESSION_KEY = 'csrf_token'
CSRF_HEADER = 'X-CSRF-Token'
CSRF_FORM_FIELD = 'csrf_token'
SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS'})


def csrf_token() -> str:
    """Token da sessão atual (cria na primeira chamada)."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def rotate_csrf_token() -> str:
    """Troca o token (após login/logout, para não reaproveitar o anterior)."""
    session[CSRF_SESSION_KEY] = secrets.token_urlsafe(32)
    return session[CSRF_SESSION_KEY]


def submitted_csrf_token() -> str:
    """Token enviado: header (JSON) ou campo do formulário."""
    return request.headers.get(CSRF_HEADER) or request.form.get(CSRF_FORM_FIELD) or ''


def csrf_is_valid() -> bool:
    """True para métodos seguros ou quando o token enviado bate com o da sessão."""
    if request.method in SAFE_METHODS:
        return True
    expected = session.get(CSRF_SESSION_KEY) or ''
    sent = submitted_csrf_token()
    return bool(expected) and hmac.compare_digest(sent.encode(), expected.encode())


def csrf_protect(view):
    """Rejeita com 400 (HTML) a rota web que mudou estado sem token válido."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not csrf_is_valid():
            abort(400, description='Token CSRF ausente ou inválido.')
        return view(*args, **kwargs)
    return wrapped


def init_csrf(app: Flask) -> None:
    """Disponibiliza ``csrf_token()`` nos templates."""
    app.jinja_env.globals['csrf_token'] = csrf_token
