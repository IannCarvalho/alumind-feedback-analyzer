"""Catálogo dos provedores de LLM suportados (BYOK).

A allowlist é deliberada: o LiteLLM fala com dezenas de provedores, e alguns
usam credenciais do AMBIENTE do servidor (``bedrock/`` usa o IAM da máquina,
``ollama/`` chama um host interno). Aceitar um prefixo arbitrário vindo de
um header deixaria um cliente usar a nuvem do operador. Só os provedores
abaixo, com chave explícita, são aceitos.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    """Um provedor de LLM e como ele é configurado."""

    id: str             # prefixo do LiteLLM ("openai" em "openai/gpt-4o-mini")
    label: str          # nome para humanos
    env_key: str        # variável de ambiente com a chave do operador
    default_model: str  # modelo barato e rápido, suficiente para classificar


PROVIDERS: dict[str, Provider] = {
    provider.id: provider
    for provider in (
        Provider('openai', 'OpenAI', 'OPENAI_API_KEY', 'gpt-4o-mini'),
        Provider('anthropic', 'Anthropic', 'ANTHROPIC_API_KEY', 'claude-haiku-4-5'),
        Provider('gemini', 'Google Gemini', 'GEMINI_API_KEY', 'gemini-2.5-flash-lite'),
    )
}

# Nome de modelo sem '/', para que o provedor venha SEMPRE do nosso prefixo.
# Cobre ids como 'gpt-4o-mini', 'claude-haiku-4-5' e 'ft:gpt-4o-mini:org::id'.
MODEL_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$')


def supported_ids() -> str:
    return ', '.join(PROVIDERS)


def get_provider(provider_id: str) -> Provider:
    """Resolve um provedor da allowlist (case-insensitive)."""
    provider = PROVIDERS.get(provider_id.strip().lower())
    if provider is None:
        raise ValueError(
            f"provedor de LLM não suportado: '{provider_id}'. Use: {supported_ids()}")
    return provider


def validate_model_name(model: str) -> str:
    model = model.strip()
    if not MODEL_NAME_RE.match(model):
        raise ValueError(f"nome de modelo inválido: '{model}'")
    return model


def parse_model_ref(ref: str) -> tuple[Provider, str]:
    """Interpreta 'provedor/modelo' (ex.: 'anthropic/claude-haiku-4-5').

    O prefixo é obrigatório: 'claude-haiku-4-5' sozinho seria ambíguo.
    """
    if '/' not in ref:
        raise ValueError(
            f"use 'provedor/modelo' (ex.: 'openai/gpt-4o-mini'), recebido: '{ref}'")
    provider_id, model = ref.split('/', 1)
    provider = get_provider(provider_id)
    return provider, validate_model_name(model or provider.default_model)
