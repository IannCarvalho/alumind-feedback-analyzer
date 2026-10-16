"""Chave de ingestão do ``POST /api/feedbacks``.

Cada ingestão com chave de LLM no servidor custa dinheiro do operador, e o
rate-limit por IP só atrasa quem tem muitos IPs. Com ``INGEST_API_KEY``
definida, o POST exige ``X-API-Key`` e responde 401 ANTES de ler o corpo ou
chamar qualquer provedor (nada é gasto nem gravado por quem não tem chave).

- Sem ``INGEST_API_KEY``: aberto, como antes (dev e instalações antigas).
- Com uma ou mais chaves (vírgula = rotação): só quem enviar uma delas.
- Opcional ``INGEST_ALLOW_BYOK_WITHOUT_KEY``: também aceita, sem chave de
  ingestão, quem trouxer a própria chave de LLM nos headers ``X-LLM-*`` (e
  nesse caso a chave do servidor nunca é usada, veja ``app.llm.credentials``).

Os GET de leitura têm a regra própria ``API_READ_TOKEN`` (``app.auth``).
"""
from functools import wraps
from hmac import compare_digest

from flask import current_app, jsonify, request

from app.llm.credentials import HEADER_API_KEY, HEADER_PROVIDER

HEADER_INGEST_KEY = 'X-API-Key'

# Mínimo por chave: a chave é a única barreira contra gasto de LLM.
MIN_INGEST_KEY_LENGTH = 24


def configured_ingest_keys() -> list[str]:
    return [key for key in current_app.config.get('INGEST_API_KEYS') or [] if key]


def _valid_ingest_key(sent: str) -> bool:
    if not sent:
        return False
    sent_bytes = sent.encode()
    # Percorre todas, sem parar na primeira: o tempo não revela qual bateu.
    matches = [compare_digest(sent_bytes, key.encode()) for key in configured_ingest_keys()]
    return any(matches)


def _brings_own_llm_key() -> bool:
    return bool(request.headers.get(HEADER_PROVIDER, '').strip()
                and request.headers.get(HEADER_API_KEY, '').strip())


def ingest_authorized() -> bool:
    """True se esta requisição pode usar a ingestão."""
    if not configured_ingest_keys():
        return True
    if _valid_ingest_key(request.headers.get(HEADER_INGEST_KEY, '')):
        return True
    config = current_app.config
    return bool(
        config.get('INGEST_ALLOW_BYOK_WITHOUT_KEY')
        and config.get('BYOK_REQUEST_KEYS_ENABLED', True)
        and _brings_own_llm_key()
    )


def ingest_key_required(view):
    """401 JSON, antes de qualquer validação de corpo ou chamada de LLM."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not ingest_authorized():
            response = jsonify({
                'error': f'Envie uma chave de ingestão válida no header {HEADER_INGEST_KEY}.',
                'code': 'ingest_key_required',
            })
            response.status_code = 401
            response.headers['WWW-Authenticate'] = 'ApiKey'
            return response
        return view(*args, **kwargs)
    return wrapped
