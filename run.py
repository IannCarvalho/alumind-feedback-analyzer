import os
import sys
import logging
from app import create_app
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the application

    Environment Variables:
        FLASK_ENV: Application environment (development/production)
        FLASK_HOST: Host to bind to (default: 0.0.0.0)
        FLASK_PORT: Port to listen on (default: 5000)
        FLASK_DEBUG: Enable debug mode (default: True in development)
    """
    try:
        # Create Flask application
        app = create_app()

        # Get configuration from environment
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', str(
            Config.is_development())).lower() == 'true'

        # Log startup configuration
        logger.info(f'Starting application in {Config.FLASK_ENV} mode')
        logger.info(f'Server will listen on {host}:{port}')
        if debug:
            logger.warning('Debug mode is enabled')

        # Start the application
        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        logger.error(f'Failed to start application: {str(e)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
