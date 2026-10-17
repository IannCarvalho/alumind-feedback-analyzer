"""Compatibilidade das rotas de página antigas (Jinja), agora servidas pelo SPA.

O painel virou um SPA Vue servido na raiz (ver ``app/routes/spa.py``). As URLs
antigas que mudaram de caminho continuam existindo como **redirects** para a
rota equivalente do SPA, para não quebrar links salvos:

- ``/dashboard`` -> ``/``
- ``/feedback/<id>`` -> ``/feedbacks/<id>``

``/feedbacks`` NÃO está aqui: é o mesmo caminho da lista no SPA, então quem o
serve é o catch-all do SPA (com o filtro ``?sentiment=`` lido pela própria
tela). Um redirect dele para ele mesmo seria um loop infinito. Os dados são
servidos pela API (``/api/...``); aqui não há render de template.
"""
import uuid

from flask import Blueprint, abort, redirect

from app.auth import login_required

web = Blueprint('web', __name__)


@web.route('/dashboard')
@login_required
def dashboard():
    """URL antiga do dashboard -> raiz do SPA."""
    return redirect('/', code=301)


@web.route('/feedback/<feedback_id>')
@login_required
def feedback_detail(feedback_id: str):
    """URL antiga do detalhe -> detalhe do SPA (/feedbacks/<id>).

    Um id malformado nunca foi um feedback válido: 404, como antes.
    """
    try:
        uuid.UUID(feedback_id)
    except ValueError:
        abort(404)
    return redirect(f'/feedbacks/{feedback_id}', code=301)
