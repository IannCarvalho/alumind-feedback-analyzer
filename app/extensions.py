"""Extensões Flask compartilhadas que precisam de uma instância única.

Fica num módulo próprio para quebrar o import circular entre o app factory
(``app/__init__.py``) e os blueprints que decoram rotas com o limitador.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

# Limitador global. Sem default_limits: cada rota declara o seu próprio
# limite via decorator; rotas não decoradas ficam ilimitadas.
limiter = Limiter(key_func=get_remote_address)

# CORS aplicado apenas às rotas da API (ver init no app factory).
cors = CORS()
