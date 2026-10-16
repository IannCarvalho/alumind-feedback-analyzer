"""Agendamento do resumo semanal por e-mail.

Duas regras guiam este módulo:

1. **O job precisa de um app context.** Ele consulta o banco via
   Flask-SQLAlchemy, e a thread do APScheduler não tem contexto nenhum: sem
   ``app.app_context()`` o envio morre com "Working outside of application
   context" toda segunda-feira.
2. **Um agendador por deploy.** Cada processo que iniciasse o seu (um por
   worker do gunicorn, ou pai e filho do reloader do Flask) mandaria o
   e-mail em dobro. Por isso ele é opt-in (``SCHEDULER_ENABLED``) e há um
   processo dedicado para deploys com mais de um worker.

Formas de rodar:

- dentro do app, com ``SCHEDULER_ENABLED=true``, em deploys de processo
  único (o padrão do container: 1 worker do gunicorn com threads);
- num processo à parte: ``python -m app.scheduling``;
- sob demanda ou por um cron externo: ``flask send-weekly-summary``.
"""
import logging

import click
from apscheduler.schedulers.base import BaseScheduler
from flask import Flask

logger = logging.getLogger(__name__)

JOB_ID = 'weekly_summary_email'


def run_weekly_summary(app: Flask) -> bool:
    """Gera e envia o resumo dentro de um app context próprio.

    Returns:
        True se o e-mail foi enviado.
    """
    from app.services.email_service import send_weekly_summary_email

    with app.app_context():
        return send_weekly_summary_email()


def schedule_weekly_summary(scheduler: BaseScheduler, app: Flask) -> None:
    """Agenda o resumo para toda segunda-feira às 8h no fuso configurado."""
    timezone = app.config.get('SCHEDULER_TIMEZONE', 'America/Sao_Paulo')
    scheduler.add_job(
        run_weekly_summary,
        'cron',
        args=[app],
        day_of_week='mon',
        hour=8,
        minute=0,
        timezone=timezone,
        id=JOB_ID,
        replace_existing=True,
        # Se o processo estava fora do ar na hora, envia uma vez ao voltar
        # (dentro de 1h), em vez de pular ou acumular disparos.
        coalesce=True,
        misfire_grace_time=3600,
    )
    logger.info('Weekly summary scheduled for every Monday at 08:00 (%s)', timezone)


def register_cli(app: Flask) -> None:
    """Registra ``flask send-weekly-summary`` (teste manual ou cron externo)."""

    @app.cli.command('send-weekly-summary')
    def send_weekly_summary_command():
        """Gera e envia o resumo semanal agora."""
        if not run_weekly_summary(app):
            raise click.ClickException('Resumo semanal NAO enviado (veja o log).')
        click.echo('Resumo semanal enviado.')


def main() -> None:
    """Processo dedicado ao agendador: ``python -m app.scheduling``."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    from app import create_app
    from app.config import Config

    class DedicatedSchedulerConfig(Config):
        # Este processo JÁ É o agendador: não sobe o BackgroundScheduler do app.
        SCHEDULER_ENABLED = False

    app = create_app(DedicatedSchedulerConfig)
    scheduler = BlockingScheduler()
    schedule_weekly_summary(scheduler, app)
    logger.info('Dedicated scheduler process started')
    scheduler.start()


if __name__ == '__main__':
    main()
