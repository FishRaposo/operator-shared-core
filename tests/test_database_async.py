import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from shared_core.database import AsyncDatabaseManager, Base


class TestModel(Base):
    __tablename__ = "test_items"
    id = Column(Integer, primary_key=True)
    name = Column(String)


@pytest.mark.asyncio
async def test_async_db_manager_sqlite_session():
    db = AsyncDatabaseManager("sqlite:///:memory:")
    assert db.engine is not None

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in db.get_session():
        assert isinstance(session, AsyncSession)

    await db.close()


@pytest.mark.asyncio
async def test_async_db_manager_create_tables():
    db = AsyncDatabaseManager("sqlite:///:memory:")
    await db.create_tables()

    async for session in db.get_session():
        result = await session.execute(__import__("sqlalchemy").text("SELECT 1"))
        assert result.scalar() == 1

    await db.close()
