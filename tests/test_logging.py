from loguru import logger

from shared_core.logging import setup_logging


def test_setup_logging():
    # setup_logging should run without errors and register interceptors
    setup_logging(level="DEBUG", service_name="logging-test")
    logger.debug("Test log message after logger setup")
    # Assert logger contains handlers (standard loguru behavior)
    assert len(logger._core.handlers) > 0
