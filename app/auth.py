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

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

auth = Blueprint('auth', __name__)

# Chave usada no cookie de sessão para marcar o usuário autenticado.
SESSION_KEY = 'dashboard_authenticated'


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


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Tela de login. Com auth desligada, redireciona direto ao dashboard."""
    if not auth_enabled() or is_authenticated():
        return redirect(url_for('web.dashboard'))

    if request.method == 'POST':
        submitted = request.form.get('password', '')
        expected = _configured_password() or ''
        # compare_digest evita vazar o tamanho/igualdade por timing.
        if compare_digest(submitted, expected):
            session[SESSION_KEY] = True
            next_url = request.args.get('next') or url_for('web.dashboard')
            # Só aceita caminhos locais no next (evita open redirect).
            if not next_url.startswith('/'):
                next_url = url_for('web.dashboard')
            return redirect(next_url)
        flash('Senha incorreta.', 'danger')

    return render_template('login.html')


@auth.route('/logout', methods=['POST'])
def logout():
    """Encerra a sessão do dashboard."""
    session.pop(SESSION_KEY, None)
    return redirect(url_for('auth.login'))
