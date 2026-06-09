import pytest

from shared_core.config import BaseAppConfig
from shared_core.testing import MockDatabase, MockRedisClient


@pytest.fixture
def mock_db():
    """In-memory SQLite database for testing."""
    db = MockDatabase()
    yield db


@pytest.fixture
def mock_redis():
    """In-memory mock Redis client."""
    return MockRedisClient()


@pytest.fixture
def app_config():
    """Base configuration with test defaults."""
    return BaseAppConfig(
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        ENV="testing",
        DEBUG=False,
    )
