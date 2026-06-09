from shared_core.redis import RedisManager


def test_redis_lazy_client():
    redis_manager = RedisManager("redis://localhost:6379/0")
    assert redis_manager._client is None

    # client access triggers initialization
    client = redis_manager.client
    assert client is not None
    assert redis_manager._client is not None


def test_redis_ping_failure():
    # Points to offline port
    redis_manager = RedisManager("redis://localhost:9999/0")

    # Ping should catch connection error and return False
    connected = redis_manager.ping()
    assert connected is False
