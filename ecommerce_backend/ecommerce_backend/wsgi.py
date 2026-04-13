import os
import signal
import sys
import logging
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings.development')

application = get_wsgi_application()

logger = logging.getLogger(__name__)


def shutdown_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    
    from core.shutdown import shutdown_handlers
    for handler in shutdown_handlers:
        try:
            handler()
        except Exception as e:
            logger.error(f"Error in shutdown handler: {e}")
    
    logger.info("Shutdown complete")
    sys.exit(0)


if sys.platform != 'win32':
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
