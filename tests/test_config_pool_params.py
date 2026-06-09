from sqlalchemy import text

from shared_core.database import DatabaseManager


def test_db_manager_accepts_pool_params():
    db = DatabaseManager(
        "sqlite:///:memory:",
        pool_size=3,
        max_overflow=5,
        pool_timeout=10,
    )

    assert db.engine is not None
    assert db.SessionLocal is not None

    session = next(db.get_session())
    result = session.execute(text("SELECT 1"))
    assert result.scalar() == 1
    session.close()
