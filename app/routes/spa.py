"""Serve o front Vue (build do Vite) a partir de ``app/static/spa``.

Aditivo e sem quebrar nada: o painel Jinja atual continua em ``/`` e
``/dashboard``. O SPA vive sob ``/app`` (protegido pelo mesmo login de
sessão) e os assets em ``/static/spa`` (gerados pelo ``vite build``). Quando
o front estiver completo, as rotas Jinja saem e o SPA assume ``/``.

Se o build ainda não existe (``vite build`` não rodou), ``/app`` responde um
aviso claro em vez de 404, para não confundir com rota inexistente.
"""
import os

from flask import Blueprint, abort, current_app, send_from_directory

from app.auth import login_required

spa = Blueprint('spa', __name__)


def _spa_dir() -> str:
    return os.path.join(current_app.static_folder, 'spa')


def _index_path() -> str:
    return os.path.join(_spa_dir(), 'index.html')


@spa.route('/app')
@spa.route('/app/')
@spa.route('/app/<path:_subpath>')
@login_required
def serve_spa(_subpath: str = ''):
    """Entrega o index do SPA; o roteamento fino é do Vue Router (history)."""
    index = _index_path()
    if not os.path.isfile(index):
        abort(
            503,
            description=(
                'O front ainda não foi compilado. Rode "npm --prefix frontend '
                'ci && npm --prefix frontend run build" para gerar app/static/spa.'
            ),
        )
    return send_from_directory(_spa_dir(), 'index.html')
