"""Chaves de provedor salvas pelo operador (cifradas), usadas pela cadeia de LLM."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app import db
from app.models.feedback import as_utc
from app.models.types import GUID


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProviderCredential(db.Model):
    """Uma chave de provedor + o modelo em que ela é usada.

    ``encrypted_key`` guarda o token Fernet (texto); a chave em claro nunca
    é gravada nem devolvida pela API: só ``key_hint`` (últimos caracteres).
    Menor ``priority`` = usada antes na cadeia (1 = principal).
    """
    __tablename__ = 'provider_credentials'
    __table_args__ = (
        UniqueConstraint('provider', 'model', name='uq_provider_credentials_provider_model'),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_hint: Mapped[str] = mapped_column(String(16), nullable=False)
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    # auth | rate_limit | timeout | connection | ... ; None = último teste ok.
    last_error_kind: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    def __repr__(self) -> str:
        # Sem encrypted_key: nada sensível em logs.
        return f'<ProviderCredential {self.provider}/{self.model}>'

    def to_dict(self) -> dict:
        """Representação pública: NUNCA inclui a chave (nem cifrada)."""
        return {
            'id': str(self.id),
            'provider': self.provider,
            'model': self.model,
            'priority': self.priority,
            'enabled': self.enabled,
            'key_hint': self.key_hint,
            'last_verified_at': as_utc(self.last_verified_at).isoformat()
            if self.last_verified_at else None,
            'last_error_kind': self.last_error_kind,
            'created_at': as_utc(self.created_at).isoformat(),
        }
