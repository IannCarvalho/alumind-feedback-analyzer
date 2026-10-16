"""Comandos de manutenção do cofre de chaves (``flask ...``)."""
import click
from flask import Flask

from app import db
from app.llm.vault import VaultDecryptError, VaultDisabledError


def register_vault_cli(app: Flask) -> None:
    """Registra ``flask rotate-llm-keys``."""

    @app.cli.command('rotate-llm-keys')
    def rotate_llm_keys_command():
        """Recifra as chaves salvas com a chave PRIMÁRIA (a primeira da lista).

        Rotação sem parar o app: (1) ponha a chave nova ANTES da antiga em
        FEEDLENS_ENCRYPTION_KEY ("nova,antiga") e reinicie; (2) rode este
        comando; (3) remova a antiga da variável.
        """
        from app.models.provider_credential import ProviderCredential
        from app.services.credential_store import get_vault

        vault = get_vault()
        if not vault.enabled:
            raise click.ClickException(str(VaultDisabledError()))
        rows = db.session.query(ProviderCredential).all()
        failed = 0
        for row in rows:
            try:
                row.encrypted_key = vault.rotate(row.encrypted_key)
            except VaultDecryptError:
                failed += 1
                click.echo(f'NAO recifrada: {row.provider}/{row.model} ({row.id})', err=True)
        db.session.commit()
        click.echo(f'{len(rows) - failed} chave(s) recifrada(s).')
        if failed:
            raise click.ClickException(f'{failed} chave(s) não puderam ser decifradas.')
