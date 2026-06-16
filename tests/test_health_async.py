import pytest

from shared_core.database import AsyncDatabaseManager
from shared_core.health import async_check_health
from shared_core.testing import MockRedisClient


class _RedisManagerStub:
    """Wraps the in-memory mock client to expose a sync ping()."""

    def __init__(self) -> None:
        self._client = MockRedisClient()

    def ping(self) -> bool:
        return self._client.ping()


@pytest.mark.asyncio
async def test_async_check_health_healthy():
    db = AsyncDatabaseManager("sqlite:///:memory:")
    await db.create_tables()
    result = await async_check_health(db, _RedisManagerStub(), "svc")
    assert result["status"] == "healthy"
    assert result["service"] == "svc"
    assert result["dependencies"]["database"] == "online"
    assert result["dependencies"]["redis"] == "online"
    await db.close()


@pytest.mark.asyncio
async def test_async_check_health_no_redis_is_online():
    db = AsyncDatabaseManager("sqlite:///:memory:")
    await db.create_tables()
    result = await async_check_health(db, None, "svc")
    assert result["dependencies"]["redis"] == "online"
    assert result["status"] == "healthy"
    await db.close()
