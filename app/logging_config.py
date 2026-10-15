"""Configuração central de logging.

Substitui o ``basicConfig(level=INFO)`` cru por um formato consistente
(timestamp, nível, logger e mensagem) e um nível configurável via env
(``LOG_LEVEL``). Idempotente: reconfigura os handlers do root logger a cada
chamada, então criar o app mais de uma vez (ex nos testes) não duplica saída.
"""
import logging
import os

LOG_FORMAT = '%(asctime)s %(levelname)-8s [%(name)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def configure_logging() -> None:
    """Configura o root logger com um formato consistente e nível por env."""
    level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(level)
    # Evita handlers duplicados quando o app é criado mais de uma vez.
    root.handlers = [handler]
