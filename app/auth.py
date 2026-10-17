"""
Autenticação do dashboard (rotas web)

Modelo de acesso: senha única compartilhada, definida em
``DASHBOARD_PASSWORD``. O dashboard é uma visão de leitura destinada
ao dono do produto, então um sistema completo de contas seria
excessivo. A sessão é guardada num cookie assinado pela ``SECRET_KEY``
do Flask.

Fail-safe: se ``DASHBOARD_PASSWORD`` não estiver definida, a proteção
fica DESLIGADA e o dashboard permanece aberto (comportamento histórico,
útil em desenvolvimento). Em produção sem senha, um aviso é registrado.
"""
from functools import wraps
from hmac import compare_digest
from urllib.parse import urlsplit

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.csrf import csrf_is_valid, rotate_csrf_token
from app.extensions import limiter

auth = Blueprint('auth', __name__)

# Chave usada no cookie de sessão para marcar o usuário autenticado.
SESSION_KEY = 'dashboard_authenticated'


def safe_next_url(target: str | None) -> str:
    """Devolve ``target`` apenas se for um caminho LOCAL; senão, o dashboard.

    Checar só ``startswith('/')`` não basta: ``//evil.com`` é uma URL
    relativa ao protocolo (host externo) e os navegadores tratam ``\\`` como
    ``/`` e descartam tab/quebra de linha, então ``/\\evil.com`` e
    ``/\\t/evil.com`` também viram ``//evil.com``.
    """
    fallback = url_for('web.dashboard')
    if not target:
        return fallback
    if '\\' in target or any(ord(char) < 32 for char in target):
        return fallback
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return fallback
    if not target.startswith('/') or target.startswith('//'):
        return fallback
    return target


def _configured_password() -> str | None:
    """Retorna a senha configurada do dashboard, ou None se ausente."""
    password = current_app.config.get('DASHBOARD_PASSWORD')
    return password or None


def auth_enabled() -> bool:
    """A proteção só é aplicada quando há uma senha configurada."""
    return _configured_password() is not None


def is_authenticated() -> bool:
    """True se a sessão atual já passou pelo login (ou se a auth está off)."""
    if not auth_enabled():
        return True
    return bool(session.get(SESSION_KEY))


def login_required(view):
    """Protege uma rota web: redireciona para o login quando não autenticado."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('auth.login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _configured_api_token() -> str | None:
    """Token de leitura da API (``API_READ_TOKEN``), ou None se ausente."""
    return current_app.config.get('API_READ_TOKEN') or None


def read_api_open() -> bool:
    """A API de leitura só fica aberta se NADA estiver configurado (dev)."""
    return not auth_enabled() and _configured_api_token() is None


def _bearer_token() -> str:
    scheme, _, value = request.headers.get('Authorization', '').partition(' ')
    return value.strip() if scheme.lower() == 'bearer' else ''


def api_read_allowed() -> bool:
    """True se a requisição pode ler a API.

    Aceita, nesta ordem: API aberta (nada configurado, comportamento
    histórico de dev), ``Authorization: Bearer <API_READ_TOKEN>`` (clientes
    servidor-a-servidor) ou a sessão do painel (frontend da mesma origem).
    """
    if read_api_open():
        return True
    token = _configured_api_token()
    sent = _bearer_token()
    if token and sent and compare_digest(sent.encode(), token.encode()):
        return True
    return auth_enabled() and bool(session.get(SESSION_KEY))


def api_read_required(view):
    """Protege os GET da API de feedbacks: 401 JSON (sem redirect) se negado."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not api_read_allowed():
            response = jsonify({
                'error': 'Autenticação necessária para ler os feedbacks.',
                'code': 'unauthenticated',
            })
            response.status_code = 401
            response.headers['WWW-Authenticate'] = 'Bearer'
            return response
        return view(*args, **kwargs)
    return wrapped


@auth.route('/login', methods=['GET', 'POST'])
# Só o POST conta: limita a força-bruta da senha sem travar o GET da tela.
@limiter.limit(
    lambda: current_app.config.get('RATELIMIT_LOGIN', '10 per minute'),
    methods=['POST'],
)
def login():
    """Tela de login. Com auth desligada, redireciona direto ao dashboard."""
    if not auth_enabled() or is_authenticated():
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        if not csrf_is_valid():
            flash('Sua sessão expirou. Tente entrar de novo.', 'warning')
            return render_template('login.html'), 400
        submitted = request.form.get('password', '')
        expected = _configured_password() or ''
        # compare_digest evita vazar o tamanho/igualdade por timing.
        if compare_digest(submitted.encode(), expected.encode()):
            # Sessão nova no login (evita fixação de sessão) e token CSRF novo.
            # "Permanente" = expira após PERMANENT_SESSION_LIFETIME, em vez
            # dos 31 dias default de um cookie assinado.
            session.clear()
            session.permanent = True
            session[SESSION_KEY] = True
            rotate_csrf_token()
            return redirect(safe_next_url(request.args.get('next')))
        flash('Senha incorreta.', 'danger')

    return render_template('login.html')


@auth.route('/logout', methods=['GET', 'POST'])
def logout():
    """Encerra a sessão do painel e volta para o login.

    Sem CSRF de propósito: logout é idempotente e seguro — o pior que um
    "logout forjado" faria é deslogar a própria vítima, sem ler nem alterar
    dado nenhum. Em troca, nunca mostramos a tela crua de 400: digitar
    /logout na barra (GET) ou um POST sem token válido (sessão expirada,
    servidor reiniciado com SECRET_KEY nova) sempre resulta em sair e ser
    redirecionado, que é exatamente o que o usuário quer ao clicar em Sair.
    """
    session.clear()
    return redirect(url_for('auth.login'))
