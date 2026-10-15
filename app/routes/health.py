"""Endpoint de health check para orquestradores (Docker, Render, etc.).

Fica fora do prefixo /api e sem autenticação, pois precisa responder a probes
antes de qualquer login. Verifica a conectividade com o banco: 200 quando o
``SELECT 1`` responde, 503 quando a conexão falha.
"""
from flask import Blueprint, jsonify
from sqlalchemy import text

from app import db

health = Blueprint('health', __name__)


@health.route('/health', methods=['GET'])
def healthcheck():
    """Readiness/liveness probe: valida o app e a conexão com o banco."""
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ok', 'database': 'ok'}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'status': 'degraded', 'database': 'error'}), 503
