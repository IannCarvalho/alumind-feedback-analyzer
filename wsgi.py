"""WSGI entry point for production servers (e.g. gunicorn).

Exposes a module-level ``app`` callable so it can be served with:

    gunicorn wsgi:app
"""
from app import create_app

app = create_app()
