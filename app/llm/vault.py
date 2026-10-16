"""Cofre das chaves de provedor salvas no banco (cifradas em repouso).

As chaves são cifradas com Fernet (AES-128-CBC + HMAC) usando
``FEEDLENS_ENCRYPTION_KEY``, que é SEPARADA da ``SECRET_KEY`` do Flask: quem
vazar o cookie de sessão não ganha as chaves dos provedores, e trocar uma não
invalida a outra. Várias chaves separadas por vírgula formam um
``MultiFernet``: a primeira cifra, todas decifram. Isso permite rotacionar
sem parar o app (veja ``flask rotate-llm-keys``).

Sem ``FEEDLENS_ENCRYPTION_KEY`` o cofre fica DESLIGADO: a API de chaves
responde 503 e nada é gravado em claro como alternativa.

Gere uma chave com::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import logging
from typing import Mapping, Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.llm.errors import LLMError

logger = logging.getLogger(__name__)

# Quantos caracteres finais da chave aparecem na interface ("...a1b2").
KEY_HINT_CHARS = 4


class VaultDisabledError(LLMError):
    """FEEDLENS_ENCRYPTION_KEY não está definida."""

    def __init__(self):
        super().__init__('cofre de chaves desligado: defina FEEDLENS_ENCRYPTION_KEY')


class VaultDecryptError(LLMError):
    """Chave salva que nenhuma FEEDLENS_ENCRYPTION_KEY atual consegue decifrar."""


def parse_fernet_keys(raw: Optional[str]) -> list[Fernet]:
    """Interpreta a variável (uma ou várias chaves). Levanta ValueError se inválida."""
    keys = [part.strip() for part in (raw or '').split(',') if part.strip()]
    fernets = []
    for index, key in enumerate(keys, start=1):
        try:
            fernets.append(Fernet(key.encode()))
        except (ValueError, TypeError):
            # Nunca inclui o valor na mensagem: é um segredo.
            raise ValueError(
                f'FEEDLENS_ENCRYPTION_KEY: a chave #{index} não é uma chave Fernet '
                f'válida (32 bytes em base64 urlsafe)') from None
    return fernets


class Vault:
    """Cifra e decifra chaves de API."""

    def __init__(self, raw_keys: Optional[str]):
        fernets = parse_fernet_keys(raw_keys)
        self._multi = MultiFernet(fernets) if fernets else None

    @classmethod
    def from_settings(cls, settings: Mapping[str, object]) -> 'Vault':
        return cls(settings.get('FEEDLENS_ENCRYPTION_KEY') or '')  # type: ignore[arg-type]

    @property
    def enabled(self) -> bool:
        return self._multi is not None

    def encrypt(self, api_key: str) -> str:
        if self._multi is None:
            raise VaultDisabledError()
        return self._multi.encrypt(api_key.encode()).decode()

    def decrypt(self, token: str) -> str:
        if self._multi is None:
            raise VaultDisabledError()
        try:
            return self._multi.decrypt(token.encode()).decode()
        except InvalidToken:
            raise VaultDecryptError(
                'não foi possível decifrar a chave salva: FEEDLENS_ENCRYPTION_KEY mudou?'
            ) from None

    def rotate(self, token: str) -> str:
        """Recifra ``token`` com a chave primária (primeira da lista)."""
        if self._multi is None:
            raise VaultDisabledError()
        try:
            return self._multi.rotate(token.encode()).decode()
        except InvalidToken:
            raise VaultDecryptError(
                'não foi possível decifrar a chave salva: FEEDLENS_ENCRYPTION_KEY mudou?'
            ) from None


def key_hint(api_key: str) -> str:
    """Só o final da chave, para o usuário reconhecer qual é (``...a1b2``)."""
    return '...' + api_key[-KEY_HINT_CHARS:]
