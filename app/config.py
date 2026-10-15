import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean value from environment variable"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() == 'true'


def get_env_int(key: str, default: int) -> int:
    """Get an integer value from environment variable"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_list(key: str, default: List[str] = None, separator: str = ',') -> List[str]:
    """Get a list of values from environment variable"""
    value = os.environ.get(key)
    if not value:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


class Config:
    """Application configuration

    Attributes:
        SECRET_KEY: Flask secret key for session management
        FLASK_ENV: Current environment (development/production)
        SQLALCHEMY_DATABASE_URI: Database connection string
        SQLALCHEMY_TRACK_MODIFICATIONS: Whether to track model modifications
        OPENAI_API_KEY: OpenAI API key for sentiment analysis
        OPENAI_MODEL: OpenAI model to use
        EMAIL_*: Email server configuration
        EMAIL_RECIPIENTS: List of email addresses for weekly summary
    """

    # Flask configuration
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'default-secret-key')
    FLASK_ENV: str = os.environ.get('FLASK_ENV', 'development')

    # Senha de acesso ao dashboard (rotas web). Se vazia, o dashboard
    # fica aberto (comportamento histórico, útil em desenvolvimento).
    DASHBOARD_PASSWORD: Optional[str] = os.environ.get('DASHBOARD_PASSWORD')

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL', 'sqlite:///feedlens.db')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # OpenAI configuration
    OPENAI_API_KEY: Optional[str] = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL: str = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    # Email configuration
    EMAIL_HOST: Optional[str] = os.environ.get('EMAIL_HOST')
    EMAIL_PORT: int = get_env_int('EMAIL_PORT', 587)
    EMAIL_USER: Optional[str] = os.environ.get('EMAIL_USER')
    EMAIL_PASSWORD: Optional[str] = os.environ.get('EMAIL_PASSWORD')
    EMAIL_USE_TLS: bool = get_env_bool('EMAIL_USE_TLS', True)

    # Email recipients for weekly summary
    EMAIL_RECIPIENTS: List[str] = get_env_list('EMAIL_RECIPIENTS')

    # Rate limiting (Flask-Limiter)
    # Liga/desliga o limitador globalmente (desligado nos testes).
    RATELIMIT_ENABLED: bool = get_env_bool('RATELIMIT_ENABLED', True)
    # Backend de armazenamento. 'memory://' serve para single-process; em
    # produção com múltiplos workers aponte para um Redis (ex redis://...).
    RATELIMIT_STORAGE_URI: str = os.environ.get(
        'RATELIMIT_STORAGE_URI', 'memory://')
    # Limite aplicado ao endpoint público de ingestão (POST /api/feedbacks).
    RATELIMIT_INGEST: str = os.environ.get(
        'RATELIMIT_INGEST', '30 per minute')

    # CORS: origens permitidas para /api/* (lista separada por vírgula).
    # Default '*' porque a API é pública (ingestão + consulta de feedbacks).
    CORS_ORIGINS: List[str] = get_env_list('CORS_ORIGINS', ['*'])

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.FLASK_ENV == 'development'

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.FLASK_ENV == 'production'

    @classmethod
    def has_email_config(cls) -> bool:
        """Check if email configuration is complete"""
        return all([
            cls.EMAIL_HOST,
            cls.EMAIL_USER,
            cls.EMAIL_PASSWORD,
            cls.EMAIL_RECIPIENTS
        ])
