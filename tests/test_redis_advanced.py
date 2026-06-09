import pytest

from shared_core.redis import RedisLock, RedisManager, cache
from shared_core.testing import MockRedisClient


class MockRedisManager(RedisManager):
    def __init__(self):
        super().__init__("redis://localhost:6379/0")
        self._client = MockRedisClient()


def test_redis_cache_sync():
    manager = MockRedisManager()

    call_count = 0

    @cache(manager, expire=10, key_prefix="test")
    def compute(x: int) -> dict:
        nonlocal call_count
        call_count += 1
        return {"value": x * 2}

    # First call: hits original function
    res1 = compute(5)
    assert res1 == {"value": 10}
    assert call_count == 1

    # Second call: returns cached result
    res2 = compute(5)
    assert res2 == {"value": 10}
    assert call_count == 1

    # Different input: hits original function
    res3 = compute(6)
    assert res3 == {"value": 12}
    assert call_count == 2


@pytest.mark.asyncio
async def test_redis_cache_async():
    manager = MockRedisManager()
    call_count = 0

    @cache(manager, expire=10, key_prefix="test")
    async def compute_async(x: int) -> dict:
        nonlocal call_count
        call_count += 1
        return {"value": x * 3}

    res1 = await compute_async(5)
    assert res1 == {"value": 15}
    assert call_count == 1

    res2 = await compute_async(5)
    assert res2 == {"value": 15}
    assert call_count == 1


def test_redis_lock_sync():
    manager = MockRedisManager()

    # Acquire lock
    with RedisLock(
        manager, "critical-lock", expire_seconds=5, acquire_timeout=1
    ) as lock:
        assert lock.acquired is True
        # Try to acquire lock again (should fail with TimeoutError)
        with pytest.raises(TimeoutError):
            with RedisLock(
                manager, "critical-lock", expire_seconds=5, acquire_timeout=0.2
            ):
                pass

    # Lock is released on exit, so we should be able to acquire it again
    with RedisLock(
        manager, "critical-lock", expire_seconds=5, acquire_timeout=1
    ) as lock:
        assert lock.acquired is True


@pytest.mark.asyncio
async def test_redis_lock_async():
    manager = MockRedisManager()

    async with RedisLock(
        manager, "async-lock", expire_seconds=5, acquire_timeout=1
    ) as lock:
        assert lock.acquired is True

        with pytest.raises(TimeoutError):
            async with RedisLock(
                manager, "async-lock", expire_seconds=5, acquire_timeout=0.2
            ):
                pass

    async with RedisLock(
        manager, "async-lock", expire_seconds=5, acquire_timeout=1
    ) as lock:
        assert lock.acquired is True
