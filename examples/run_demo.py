import os
import sys

from loguru import logger

# Add src to system path to run example locally without install
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from shared_core.config import BaseAppConfig
from shared_core.database import DatabaseManager
from shared_core.errors import BaseApplicationError, ValidationError
from shared_core.health import check_health
from shared_core.logging import setup_logging
from shared_core.redis import RedisManager


def run_shared_core_demo():
    # 1. Initialize Loguru Logging
    setup_logging(level="INFO", service_name="shared-core-demo")
    logger.info("Starting Shared Core Demonstration")

    # 2. Config Parsing
    logger.info("Initializing configuration manager...")
    config = BaseAppConfig()
    logger.info(
        f"Loaded Config - APP_NAME: {config.APP_NAME}, "
        f"ENV: {config.ENV}, DEBUG: {config.DEBUG}"
    )

    # 3. Database Manager Initialization
    logger.info(f"Connecting to database engine via URL: {config.DATABASE_URL}...")
    db_manager = DatabaseManager(config.DATABASE_URL)

    # 4. Redis Manager Initialization
    logger.info(f"Connecting to Redis client pool via URL: {config.REDIS_URL}...")
    redis_manager = RedisManager(config.REDIS_URL)

    # 5. Core Error Ingestion & Custom Exceptions
    logger.info("Verifying custom exception handlers...")
    try:
        raise ValidationError("This is a simulated input validation error.")
    except BaseApplicationError as e:
        logger.warning(
            f"Caught Application Error: {e.code} | "
            f"Message: {e.message} | Status: {e.status_code}"
        )

    # 6. Dependency Health Monitoring
    logger.info("Evaluating dependencies connectivity...")
    health_result = check_health(db_manager, redis_manager, "shared-core-demo")
    logger.info(f"Health Status Result: {health_result['status']}")
    logger.info(f"  Database Status: {health_result['dependencies']['database']}")
    logger.info(f"  Redis Status: {health_result['dependencies']['redis']}")

    logger.info("Shared Core Demonstration Finished successfully.")


if __name__ == "__main__":
    run_shared_core_demo()
