"""Compatibilidade das rotas de página antigas (Jinja), agora servidas pelo SPA.

O painel virou um SPA Vue servido na raiz (ver ``app/routes/spa.py``). As URLs
antigas renderizadas por Jinja (``/dashboard``, ``/feedbacks``,
``/feedback/<id>``) continuam existindo como **redirects** para a rota
equivalente do SPA, para não quebrar links salvos nem o link do e-mail do
resumo semanal. Os dados são servidos pela API (``/api/...``); aqui não há
mais render de template.
"""
import uuid

from flask import Blueprint, redirect, request
from app.auth import login_required

web = Blueprint('web', __name__)


@web.route('/dashboard')
@login_required
def dashboard():
    """URL antiga do dashboard -> raiz do SPA."""
    return redirect('/', code=301)


@web.route('/feedbacks')
@login_required
def feedback_list():
    """URL antiga da lista -> lista do SPA, preservando o filtro de sentimento."""
    sentiment = request.args.get('sentiment')
    target = '/feedbacks'
    if sentiment:
        target = f'/feedbacks?sentiment={sentiment}'
    return redirect(target, code=301)


@web.route('/feedback/<feedback_id>')
@login_required
def feedback_detail(feedback_id: str):
    """URL antiga do detalhe -> detalhe do SPA (/feedbacks/<id>).

    Um id malformado nunca foi um feedback válido: 404, como antes.
    """
    try:
        uuid.UUID(feedback_id)
    except ValueError:
        from flask import abort
        abort(404)
    return redirect(f'/feedbacks/{feedback_id}', code=301)
