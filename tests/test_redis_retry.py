from unittest.mock import MagicMock, patch

import redis

from shared_core.redis import RedisManager


def test_redis_connect_retry_success_on_first_attempt():
    mgr = RedisManager("redis://localhost:6379/0")
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mgr._client = mock_client

    mgr.connect(max_retries=3)
    assert mock_client.ping.call_count == 1


def test_redis_connect_retry_success_on_second_attempt():
    mgr = RedisManager("redis://localhost:6379/0")
    mock_client = MagicMock()
    mock_client.ping.side_effect = [
        redis.ConnectionError("fail"),
        True,
    ]
    mgr._client = mock_client

    with patch("time.sleep", return_value=None):
        mgr.connect(max_retries=3, backoff_factor=0.01)

    assert mock_client.ping.call_count == 2


def test_redis_connect_retry_exhausted():
    mgr = RedisManager("redis://localhost:6379/0")
    mock_client = MagicMock()
    mock_client.ping.side_effect = redis.ConnectionError("fail")
    mgr._client = mock_client

    with patch("time.sleep", return_value=None):
        try:
            mgr.connect(max_retries=2, backoff_factor=0.01)
            raise AssertionError("Expected ConnectionError")
        except redis.ConnectionError:
            pass

    assert mock_client.ping.call_count == 2
