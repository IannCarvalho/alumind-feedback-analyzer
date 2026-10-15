from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Type
import logging

from app.config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
scheduler = BackgroundScheduler()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_config(config: Type[Config]) -> None:
    """
    Validate application configuration

    Args:
        config: Configuration class to validate

    Raises:
        ValueError: If required configuration is missing
    """
    # Check required Flask configuration
    if not config.SECRET_KEY or config.SECRET_KEY == 'default-secret-key':
        logger.warning(
            'Using default secret key. This is not secure for production.')

    # Check OpenAI configuration
    if not config.OPENAI_API_KEY:
        raise ValueError('OPENAI_API_KEY must be set')

    # Check email configuration if in production
    if config.is_production() and not config.has_email_config():
        raise ValueError('Email configuration is required in production')

    # Warn when the dashboard is left open in production
    if config.is_production() and not config.DASHBOARD_PASSWORD:
        logger.warning(
            'DASHBOARD_PASSWORD is not set. The dashboard is publicly '
            'accessible without authentication.')


def init_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions

    Args:
        app: Flask application instance
    """
    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app: Flask) -> None:
    """
    Register application blueprints

    Args:
        app: Flask application instance
    """
    from app.routes.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from app.routes.web import web as web_blueprint
    app.register_blueprint(web_blueprint)

    from app.routes.health import health as health_blueprint
    app.register_blueprint(health_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.auth import auth_enabled

    @app.context_processor
    def inject_auth_flags():
        """Disponibiliza o estado da autenticação para os templates."""
        return {'auth_enabled': auth_enabled()}


def init_scheduler(app: Flask) -> None:
    """
    Initialize background task scheduler

    Args:
        app: Flask application instance
    """
    with app.app_context():
        if not scheduler.running:
            from app.services.email_service import schedule_weekly_summary
            try:
                schedule_weekly_summary(scheduler)
                scheduler.start()
                logger.info('Background scheduler started successfully')
            except Exception as e:
                logger.error(f'Failed to start scheduler: {str(e)}')


def create_app(config_class: Type[Config] = Config) -> Flask:
    """
    Create and configure the Flask application

    Args:
        config_class: Configuration class to use

    Returns:
        Configured Flask application

    Raises:
        ValueError: If required configuration is missing
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_class)

    try:
        # Validate configuration
        validate_config(config_class)

        # Initialize components
        init_extensions(app)
        register_blueprints(app)
        init_scheduler(app)

        logger.info(f'Application started in {config_class.FLASK_ENV} mode')

    except Exception as e:
        logger.error(f'Failed to initialize application: {str(e)}')
        raise

    return app

# Import models for Flask-Migrate to detect them
