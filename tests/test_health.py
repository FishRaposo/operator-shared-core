from unittest.mock import MagicMock

from shared_core.health import check_health


def test_check_health_healthy():
    # Mock DatabaseManager
    mock_db = MagicMock()
    # Mock RedisManager
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True

    result = check_health(mock_db, mock_redis, "health-check-test")

    assert result["status"] == "healthy"
    assert result["service"] == "health-check-test"
    assert result["dependencies"]["database"] == "online"
    assert result["dependencies"]["redis"] == "online"


def test_check_health_degraded():
    # Mock DatabaseManager throwing exception on session local execution
    mock_db = MagicMock()
    mock_db.SessionLocal.side_effect = Exception("DB offline")

    # Mock RedisManager returning False on ping
    mock_redis = MagicMock()
    mock_redis.ping.return_value = False

    result = check_health(mock_db, mock_redis, "health-check-test")

    assert result["status"] == "degraded"
    assert result["dependencies"]["database"] == "offline"
    assert result["dependencies"]["redis"] == "offline"
