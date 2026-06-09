from shared_core.redis import RedisManager


def test_redis_close_nullifies_client():
    mgr = RedisManager("redis://localhost:6379/0")
    assert mgr._client is None

    _ = mgr.client
    assert mgr._client is not None

    mgr.close()
    assert mgr._client is None


def test_redis_close_idempotent():
    mgr = RedisManager("redis://localhost:6379/0")
    mgr.close()
    mgr.close()
    assert mgr._client is None
