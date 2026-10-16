"""Erros da camada de LLM, independentes do LiteLLM."""
from dataclasses import dataclass


class LLMError(Exception):
    """Base dos erros da camada de LLM."""


class LLMNotConfiguredError(LLMError):
    """Nenhum provedor utilizável: sem chave no servidor e sem BYOK na requisição."""

    def __init__(self):
        super().__init__('nenhum provedor de LLM configurado')


@dataclass(frozen=True)
class Attempt:
    """Uma tentativa falha na cadeia de provedores (mensagem já sem a chave)."""

    model_ref: str
    kind: str      # auth | rate_limit | timeout | connection | not_found | bad_request | empty | error
    detail: str


class LLMRequestError(LLMError):
    """Todos os candidatos da cadeia falharam."""

    def __init__(self, attempts: list[Attempt]):
        self.attempts = attempts
        summary = '; '.join(f'{a.model_ref}: {a.kind}' for a in attempts)
        super().__init__(f'todas as chamadas à LLM falharam ({summary})')

    @property
    def auth_failed(self) -> bool:
        """True quando TODA falha foi de credencial (chave recusada)."""
        return bool(self.attempts) and all(a.kind == 'auth' for a in self.attempts)


class ByokHeaderError(ValueError):
    """Headers X-LLM-* inválidos na requisição."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
