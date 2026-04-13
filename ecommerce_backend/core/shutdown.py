import signal
import sys
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

shutdown_handlers: List[Callable] = []


def register_shutdown_handler(handler: Callable):
    shutdown_handlers.append(handler)
    logger.info(f"Registered shutdown handler: {handler.__name__}")


def graceful_shutdown_handler(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    
    for handler in shutdown_handlers:
        try:
            handler()
            logger.info(f"Executed shutdown handler: {handler.__name__}")
        except Exception as e:
            logger.error(f"Error in shutdown handler {handler.__name__}: {e}")

    logger.info("Graceful shutdown complete")
    sys.exit(0)


def setup_graceful_shutdown():
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, graceful_shutdown_handler)
        signal.signal(signal.SIGINT, graceful_shutdown_handler)
    
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, graceful_shutdown_handler)
    
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, graceful_shutdown_handler)
    
    logger.info("Graceful shutdown handlers registered")


class GracefulShutdownMixin:
    shutdown_called = False

    def shutdown(self):
        if self.shutdown_called:
            return
        self.shutdown_called = True
        
        logger.info(f"Initiating shutdown for {self.__class__.__name__}")
        self.on_shutdown()
        
        for handler in shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in shutdown: {e}")

    def on_shutdown(self):
        pass
