"""Testes da configuração de logging estruturado."""
import logging

from app.logging_config import configure_logging, LOG_FORMAT


def test_configure_logging_installs_single_handler():
    """Chamar duas vezes não duplica handlers no root logger."""
    configure_logging()
    configure_logging()
    root = logging.getLogger()
    assert len(root.handlers) == 1


def test_handler_uses_structured_format():
    """O handler usa o formato consistente definido no módulo."""
    configure_logging()
    handler = logging.getLogger().handlers[0]
    assert handler.formatter._fmt == LOG_FORMAT


def test_log_level_from_env(monkeypatch):
    """O nível do root logger respeita LOG_LEVEL."""
    monkeypatch.setenv('LOG_LEVEL', 'WARNING')
    configure_logging()
    assert logging.getLogger().level == logging.WARNING
    # Restaura para não afetar outros testes.
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    configure_logging()
