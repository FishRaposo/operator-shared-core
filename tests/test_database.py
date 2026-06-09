from sqlalchemy import text

from shared_core.database import DatabaseManager


def test_db_manager_sqlite_session():
    # SQLite memory engine
    db_manager = DatabaseManager("sqlite:///:memory:")

    # Check session Local factory exists
    assert db_manager.SessionLocal is not None

    # Test session lifecycle generator
    session_generator = db_manager.get_session()
    session = next(session_generator)

    try:
        # Run dummy query
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        # Close session
        try:
            next(session_generator)
        except StopIteration:
            pass
