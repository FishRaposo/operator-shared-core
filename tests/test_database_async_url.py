from shared_core.database import to_async_url


def test_plain_postgresql_rewritten():
    assert (
        to_async_url("postgresql://u:p@localhost:5432/db")
        == "postgresql+asyncpg://u:p@localhost:5432/db"
    )


def test_postgres_scheme_rewritten():
    assert (
        to_async_url("postgres://u:p@localhost:5432/db")
        == "postgresql+asyncpg://u:p@localhost:5432/db"
    )


def test_psycopg_rewritten():
    assert (
        to_async_url("postgresql+psycopg://u:p@localhost/db")
        == "postgresql+asyncpg://u:p@localhost/db"
    )


def test_sqlite_rewritten():
    assert to_async_url("sqlite:///./local.db") == "sqlite+aiosqlite:///./local.db"


def test_already_async_sqlite_is_idempotent():
    # Must not double-apply (the "sqlite:///" substring lives inside "aiosqlite:///").
    assert (
        to_async_url("sqlite+aiosqlite:///./data/agenttrace.db")
        == "sqlite+aiosqlite:///./data/agenttrace.db"
    )


def test_already_async_is_idempotent():
    assert (
        to_async_url("postgresql+asyncpg://u:p@localhost/db")
        == "postgresql+asyncpg://u:p@localhost/db"
    )
