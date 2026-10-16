"""WSGI entry point for production servers (e.g. gunicorn).

Exposes a module-level ``app`` callable so it can be served with:

    gunicorn wsgi:app
"""
import threading

from app import create_app
from app.llm import warm_up

app = create_app()

# O LiteLLM é importado sob demanda (~200 MB, segundos de import). No
# servidor, aquecê-lo em segundo plano poupa esse custo da primeira análise.
threading.Thread(target=warm_up, name='litellm-warm-up', daemon=True).start()
