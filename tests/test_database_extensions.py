from sqlalchemy import Column, String

from shared_core.database import (
    Base,
    BaseRepository,
    DatabaseManager,
    TimestampMixin,
    UUIDMixin,
)


class DummyModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dummy_model"
    name = Column(String(50), nullable=False)


def test_database_extensions():
    db = DatabaseManager("sqlite:///:memory:")
    # Register and create tables
    DummyModel.metadata.create_all(bind=db.engine)

    session = db.SessionLocal()
    repo = BaseRepository(DummyModel, session)

    # Test create
    item = repo.create(name="Test Item")
    assert item.id is not None
    assert len(item.id) == 36
    assert item.created_at is not None
    assert item.updated_at is not None
    assert item.name == "Test Item"

    # Test get
    fetched = repo.get(item.id)
    assert fetched is not None
    assert fetched.name == "Test Item"

    # Test list
    items = repo.list()
    assert len(items) == 1
    assert items[0].id == item.id

    # Test update
    updated = repo.update(item.id, name="New Name")
    assert updated is not None
    assert updated.name == "New Name"

    # Test delete
    deleted = repo.delete(item.id)
    assert deleted is True
    assert repo.get(item.id) is None

    session.close()
