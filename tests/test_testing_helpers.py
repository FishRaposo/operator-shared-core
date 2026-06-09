from sqlalchemy import text

from shared_core.testing import MockDatabase, MockRedisClient


def test_mock_database():
    mock_db = MockDatabase()
    assert mock_db.engine is not None
    assert mock_db.SessionLocal is not None

    session = next(mock_db.get_session())
    result = session.execute(text("SELECT 1"))
    assert result.scalar() == 1
    session.close()


def test_mock_redis_client():
    client = MockRedisClient()
    assert client.ping() is True

    # Test basic get/set
    client.set("key", "val")
    assert client.get("key") == "val"

    # Test delete
    client.delete("key")
    assert client.get("key") is None

    # Test set NX
    assert client.set("key_nx", "val1", nx=True) is True
    assert client.set("key_nx", "val2", nx=True) is False
    assert client.get("key_nx") == "val1"
