# shared-core

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green)
![SQLAlchemy 2.0](https://img.shields.io/badge/sqlalchemy-2.0-orange)
![Library Only](https://img.shields.io/badge/type-library-lightgrey)
![Tests](https://img.shields.io/badge/tests-45%20passing-brightgreen)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

**The shared foundation library powering every Python service in the Operator Systems showcase portfolio.**

## Why This Exists

Building 10+ showcase projects that each re-implement configuration loading, database connections, logging setup, error handling, Redis utilities, HTTP clients, LLM integrations, health checks, and testing harnesses would produce inconsistent, fragile code and defeat the purpose of demonstrating production-grade engineering. `shared-core` exists so that every project in the portfolio starts from the same infrastructure baseline — identical config patterns, identical error structures, identical logging output — and any improvement to the foundation automatically propagates to all consumers.

This is a **library, not a service**. It has no `main.py`, no Docker container, no API endpoints, and no independent deployment. It is installed as an editable Python package by every other project in the workspace.

## What It Demonstrates

- **Centralized configuration management** via Pydantic v2 `BaseSettings` with automatic `.env` loading, type validation, and `SecretStr` for sensitive fields
- **Database abstraction** with SQLAlchemy 2.0 engine/session lifecycle, connection pooling with `pool_pre_ping`, shared declarative `Base`, ORM mixins (`UUIDMixin`, `TimestampMixin`), and generic `BaseRepository` CRUD pattern
- **Async database support** via `AsyncDatabaseManager` using SQLAlchemy `AsyncSession` with `asyncpg` driver for projects needing non-blocking DB access
- **Structured logging** using Loguru with service-tagged, colorized, timestamped output, correlation ID propagation via contextvars, and `RequestLoggingMiddleware` for FastAPI
- **Typed error hierarchy** with 10 HTTP-aware exception classes (`NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`, `ExternalServiceError`, etc.) carrying `message`, `code`, and `status_code` — ready for FastAPI exception handlers
- **Lazy Redis connectivity** with deferred client initialization, `ping()` health check, `@cache` decorator (sync + async, MD5 key hashing), `RedisLock` distributed lock (sync + async context managers, Lua atomic release), connection retry with exponential backoff, and explicit `close()`
- **HTTP client abstraction** via `BaseHTTPClient` with async httpx, correlation ID forwarding, exponential backoff retry on 5xx errors, convenience methods (`get`/`post`/`put`/`delete`)
- **LLM integration** via `LLMClientFactory` with dynamic OpenAI/Anthropic imports, standardized `LLMResponse`, cost estimation with static rate table, and `generate_mock()` for testing
- **Celery bootstrap** via `create_celery_app()` with signal-based logging (prerun/postrun/failure), JSON serialization, and time limits
- **Health check aggregation** via `check_health()` that queries PostgreSQL and Redis and returns a standardized `{status, service, dependencies}` response
- **Observability** via `MetricsRegistry` and `MetricsMiddleware` (Prometheus-compatible, dynamically imported to keep it optional)
- **Testing harnesses** — `MockDatabase` (in-memory SQLite) and `MockRedisClient` (full mock with TTL and NX semantics) for isolated unit tests without Docker dependencies
- **Library packaging discipline** — proper `pyproject.toml`, editable installs, no circular dependencies

## Module Reference

### `shared_core.config` — Configuration Management

```python
from shared_core.config import BaseAppConfig

class MyProjectConfig(BaseAppConfig):
    CUSTOM_SETTING: str = "default"

config = MyProjectConfig()  # Reads from .env automatically
```

`BaseAppConfig` provides these fields with sensible defaults:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `APP_NAME` | `str` | `"operator-showcase"` | Service identifier for logging |
| `ENV` | `str` | `"development"` | Environment name |
| `DEBUG` | `bool` | `True` | Debug mode toggle |
| `DATABASE_URL` | `str` | `postgresql+psycopg://...` | PostgreSQL connection string |
| `REDIS_URL` | `str` | `redis://localhost:6379/0` | Redis connection string |
| `LOG_LEVEL` | `str` | `"INFO"` | Logging verbosity |
| `OPENAI_API_KEY` | `Optional[str]` | `None` | OpenAI API credential |
| `ANTHROPIC_API_KEY` | `Optional[str]` | `None` | Anthropic API credential |
| `GITHUB_TOKEN` | `Optional[str]` | `None` | GitHub API token |
| `LLM_FAST_MODEL` | `str` | `"gpt-4o-mini"` | Default fast/cheap LLM model |
| `LLM_SMART_MODEL` | `str` | `"gpt-4o"` | Default capable LLM model |
| `LLM_EMBEDDING_MODEL` | `str` | `"text-embedding-3-small"` | Default embedding model |
| `LLM_TEMPERATURE` | `float` | `0.7` | Default LLM temperature |
| `LLM_MAX_TOKENS` | `int` | `4096` | Default max completion tokens |
| `CELERY_BROKER_URL` | `str` | `redis://localhost:6379/0` | Celery message broker |
| `CELERY_RESULT_BACKEND` | `str` | `redis://localhost:6379/0` | Celery result backend |
| `CORS_ALLOWED_ORIGINS` | `str` | `"*"` | CORS allowed origins |
| `DB_POOL_SIZE` | `int` | `5` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `int` | `10` | Max overflow connections |
| `DB_POOL_TIMEOUT` | `int` | `30` | Pool connection timeout seconds |

The `model_config` uses `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`, meaning unknown environment variables are silently ignored and downstream projects can extend freely.

Includes `validate_config()` classmethod that returns a list of issues (field name, message, severity) without raising.

### `shared_core.database` — Database Layer

```python
from shared_core.database import DatabaseManager, AsyncDatabaseManager, Base, BaseRepository

# Synchronous
db = DatabaseManager(config.DATABASE_URL, pool_size=5, max_overflow=10)
session = next(db.get_session())
db.create_tables()

# Async
async_db = AsyncDatabaseManager(config.DATABASE_URL)
async for session in async_db.get_session():
    ...

# Generic CRUD repository
class ItemRepository(BaseRepository[Item]):
    pass
```

- **`DatabaseManager.__init__(db_url, pool_size, max_overflow, pool_timeout)`** — Creates a SQLAlchemy `Engine` with `pool_pre_ping=True` and configurable pool parameters
- **`DatabaseManager.get_session()`** — Generator yielding a `Session` that auto-closes on exit, compatible with FastAPI `Depends()`
- **`DatabaseManager.create_tables()`** — Calls `Base.metadata.create_all()`, idempotent
- **`AsyncDatabaseManager`** — Same API, async — uses `AsyncSession` and `asyncpg` driver. `get_session()` is an async generator, `close()` disposes the engine
- **`Base`** — The shared `declarative_base()` that all downstream ORM models must inherit from
- **`UUIDMixin`** / **`TimestampMixin`** — Standard column mixins for primary keys and audit timestamps
- **`BaseRepository[T]`** — Generic CRUD with `get()`, `list()`, `create()`, `update()`, `delete()` methods

### `shared_core.logging` — Structured Logging

```python
from shared_core.logging import setup_logging, RequestLoggingMiddleware, correlation_id_var

setup_logging(level="DEBUG", service_name="workflow-engine")
```

Configures Loguru to output structured, colorized logs to stdout:

```
2026-06-08 18:30:00.123 | INFO     | workflow-engine | abc123 | main:startup:42 - Server ready
```

- Removes all default Loguru handlers on each call (idempotent setup)
- Injects `service_name` and `correlation_id` into every log line via Loguru's `extra` context
- `RequestLoggingMiddleware` — FastAPI middleware that generates/forwards `X-Correlation-ID` headers, logs request start/completion with method, path, status, and duration
- `correlation_id_var` — ContextVar for manual correlation ID propagation across async tasks

### `shared_core.errors` — Error Hierarchy

```python
from shared_core.errors import (
    BaseApplicationError, DatabaseError, ConfigurationError,
    ExternalAPIError, ValidationError, NotFoundError,
    ConflictError, UnauthorizedError, ForbiddenError,
    ExternalServiceError, application_error_handler,
)
```

| Exception | Code | HTTP Status | Use Case |
|-----------|------|-------------|----------|
| `BaseApplicationError` | `INTERNAL_SERVER_ERROR` | 500 | Base class for all app errors |
| `DatabaseError` | `DATABASE_ERROR` | 500 | Connection failures, query errors |
| `ConfigurationError` | `CONFIGURATION_ERROR` | 500 | Missing or invalid config values |
| `ExternalAPIError` | `EXTERNAL_API_ERROR` | 502 | LLM or third-party API failures |
| `ValidationError` | `VALIDATION_ERROR` | 400 | Input validation failures |
| `NotFoundError` | `NOT_FOUND` | 404 | Resource not found |
| `ConflictError` | `CONFLICT` | 409 | Resource state conflict |
| `UnauthorizedError` | `UNAUTHORIZED` | 401 | Authentication required/failed |
| `ForbiddenError` | `FORBIDDEN` | 403 | Insufficient permissions |
| `ExternalServiceError` | `EXTERNAL_SERVICE_ERROR` | 502 | External service dependency failure |

Every exception carries `.message`, `.code`, and `.status_code` attributes. `application_error_handler` is a ready-to-use FastAPI exception handler that returns consistent JSON error responses.

### `shared_core.redis` — Redis Connectivity

```python
from shared_core.redis import RedisManager, cache, RedisLock

redis_mgr = RedisManager(config.REDIS_URL)

# Lazy connection
if redis_mgr.ping():
    redis_mgr.client.set("key", "value")

# Retry connection
redis_mgr.connect(max_retries=3)

# Clean shutdown
redis_mgr.close()

# Cache decorator (works for sync and async functions)
@cache(redis_mgr, expire=3600, key_prefix="myapp")
def expensive_computation(x: int) -> str:
    return str(x * 2)

# Distributed lock
with RedisLock(redis_mgr, "critical-section", expire_seconds=10):
    # Only one worker executes this at a time
    ...

async with RedisLock(redis_mgr, "critical-section"):
    await async_work()
```

- **Lazy initialization** — the `redis.Redis` client is only created on first `.client` access
- **`ping()`** — Returns `True`/`False` (never raises), suitable for health check endpoints
- **`connect(max_retries, backoff_factor)`** — Eagerly connect with exponential backoff retry
- **`close()`** — Explicitly close the connection pool
- **`@cache` decorator** — Caches function results with MD5-hashed argument keys, supports sync + async
- **`RedisLock`** — Distributed lock with sync and async context manager support, atomic release via Lua script
- **`decode_responses=True`** — all values returned as strings

### `shared_core.health` — Health Checks

```python
from shared_core.health import check_health

result = check_health(db_manager, redis_manager, "my-service")
# {
#     "status": "healthy",
#     "service": "my-service",
#     "dependencies": {"database": "online", "redis": "online"}
# }
```

Runs `SELECT 1` against the database and pings Redis. Returns `"healthy"` or `"degraded"` with per-dependency status.

### `shared_core.clients` — HTTP Client

```python
from shared_core.clients import BaseHTTPClient

client = BaseHTTPClient(base_url="https://api.example.com", max_retries=3)
response = await client.get("/resource")
data = await client.post("/submit", json={"key": "value"})
await client.close()
```

- Async httpx wrapper with exponential backoff retry on 5xx errors
- Automatically forwards `X-Correlation-ID` from the current context
- Convenience methods: `get`, `post`, `put`, `delete`
- Configurable timeout, max retries, and backoff factor

### `shared_core.llm` — LLM Integration

```python
from shared_core.llm import LLMClientFactory, estimate_llm_cost

factory = LLMClientFactory(
    openai_api_key=config.OPENAI_API_KEY,
    anthropic_api_key=config.ANTHROPIC_API_KEY,
)

response = await factory.generate_openai("gpt-4o-mini", "Hello!")
# LLMResponse(text="...", model="...", prompt_tokens=5, completion_tokens=3, ...)

cost = estimate_llm_cost("gpt-4o-mini", prompt_tokens=100, completion_tokens=50)
mock_response = await factory.generate_mock("gpt-4o", "test prompt")
```

- **`LLMClientFactory`** — Dynamic imports for OpenAI/Anthropic SDKs (keeps deps optional)
- **`LLMResponse`** — Standardized Pydantic model with `text`, `model`, token counts, `latency_ms`, and `estimated_cost`
- **`estimate_llm_cost()`** — Static cost table for 4 models (gpt-4o, gpt-4o-mini, claude-3-5-sonnet, claude-3-haiku)
- **`generate_mock()`** — Fast mock response for unit tests without API calls

### `shared_core.tasks` — Celery Bootstrap

```python
from shared_core.tasks import create_celery_app

app = create_celery_app("my-service", broker_url=config.CELERY_BROKER_URL)
```

- Dynamic Celery import (optional dependency)
- Pre-configured with JSON serialization, UTC timezone, task time limits
- Signal handlers automatically log task prerun, postrun, and failure events

### `shared_core.metrics` — Observability

```python
from shared_core.metrics import MetricsRegistry, MetricsMiddleware

metrics = MetricsRegistry("my-service")
app.add_middleware(MetricsMiddleware, registry=metrics)

# Expose Prometheus scrape endpoint
@app.get("/metrics")(metrics_endpoint(metrics))
```

- **`MetricsRegistry`** — Holds pre-defined Prometheus metrics: HTTP request counter, duration histogram, DB connections gauge, error counter
- **`MetricsMiddleware`** — FastAPI middleware that auto-instruments all endpoints
- Dynamic import of `prometheus_client` — keeps it optional for projects that don't need metrics

### `shared_core.testing` — Test Harnesses

```python
from shared_core.testing import MockDatabase, MockRedisClient

db = MockDatabase()          # In-memory SQLite with all Base tables created
redis = MockRedisClient()    # Full mock with get/set/setex/delete/eval, TTL, NX semantics

session = next(db.get_session())
redis.set("key", "val")
```

- **`MockDatabase`** — SQLite in-memory engine with `Base.metadata.create_all()`, same `get_session()` generator as `DatabaseManager`
- **`MockRedisClient`** — In-memory mock supporting `get`, `set` (with `ex`/`px`/`nx`), `setex`, `delete`, and `eval` (Lua lock release simulation)

## Installation

`shared-core` is consumed as an editable package. From any sibling project directory:

```bash
pip install -e ../shared-core
```

Or install with development dependencies:

```bash
pip install -e ../shared-core[dev]
```

Every project's `make install` runs this automatically.

## Project Structure

```
shared-core/
├── pyproject.toml              # Package metadata and dependencies
├── Makefile                    # install, test, lint, format, typecheck, docs, clean
├── docker-compose.yml          # Postgres (pgvector) + Redis services
├── mkdocs.yml                  # API documentation generation config
├── pytest.ini                  # Pytest settings
├── ruff.toml                   # Ruff linting rules
├── pyrightconfig.json          # Pyright type checking config
├── .env.example                # Environment variable template
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline (lint, format, typecheck, test)
├── src/
│   └── shared_core/
│       ├── __init__.py         # Package version
│       ├── config.py           # BaseAppConfig (Pydantic BaseSettings)
│       ├── database.py         # DatabaseManager, AsyncDatabaseManager, Base, mixins, BaseRepository
│       ├── errors.py           # 10-exception hierarchy + FastAPI handler
│       ├── logging.py          # setup_logging(), RequestLoggingMiddleware, correlation_id_var
│       ├── redis.py            # RedisManager, @cache decorator, RedisLock
│       ├── health.py           # check_health()
│       ├── clients.py          # BaseHTTPClient (async httpx + retry)
│       ├── llm.py              # LLMClientFactory, LLMResponse, estimate_llm_cost()
│       ├── tasks.py            # create_celery_app()
│       ├── metrics.py          # MetricsRegistry, MetricsMiddleware, metrics_endpoint()
│       └── testing.py          # MockDatabase, MockRedisClient
├── examples/
│   └── run_demo.py             # Runnable demo exercising all modules
├── tests/                      # 25+ unit tests across 14+ test files
│   └── conftest.py             # Shared fixtures (mock_db, mock_redis, app_config)
├── docs/
│   ├── architecture.md         # System overview and component diagrams
│   ├── design-decisions.md     # Architecture Decision Records (ADRs)
│   ├── failure-modes.md        # Failure mode catalog with mitigations
│   ├── roadmap.md              # Development phases and milestones
│   ├── security.md             # Security boundaries and rules
│   ├── implementation_plan.md  # Technical implementation details
│   └── api/                    # API reference stubs for mkdocs generation
├── README.md
└── AGENTS.md
```

## Available Make Targets

| Target | Command | Notes |
|--------|---------|-------|
| `make install` | `pip install -e .[dev]` | Installs library + dev tools |
| `make test` | `pytest` | Runs 25+ unit tests |
| `make lint` | `ruff check .` | Lint all source files |
| `make format` | `ruff format .` | Auto-format with ruff |
| `make typecheck` | `pyright` | Static type checking |
| `make docs` | `mkdocs build` | Generate API documentation |
| `make docker-up` | `docker compose up -d` | Start Postgres + Redis |
| `make docker-down` | `docker compose down` | Stop infrastructure |
| `make demo` | `python examples/run_demo.py` | Run demonstration script |
| `make clean` | Python shutil cleanup | Remove caches and pyc files |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic-settings` | ≥2.0.0 | `.env` file loading, typed config |
| `pydantic` | ≥2.0.0 | Data validation, model serialization |
| `sqlalchemy` | ≥2.0.0 | ORM, engine, session management |
| `pgvector` | ≥0.2.0 | Vector similarity search extension for PostgreSQL |
| `redis` | ≥5.0.0 | Redis client library |
| `loguru` | ≥0.7.0 | Structured logging with zero boilerplate |
| `httpx` | ≥0.24.0 | Async HTTP client |

Dev dependencies: `pytest`, `ruff`, `pyright`, `respx`, `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`

Optional (dynamically imported): `openai`, `anthropic`, `celery`, `prometheus_client`

## Consumer Projects

Every Python project in the portfolio depends on `shared-core`:

| Project | What It Uses |
|---------|-------------|
| `async-workflow-engine` | Config, Database, Logging, Redis, Errors, Health, Clients, Tasks |
| `llm-cost-latency-monitor` | Config, Database, Logging, Errors, LLM, Health, Clients |
| `document-intelligence-pipeline` | Config, Database, Logging, Errors, Health, Clients |
| `rag-evaluation-lab` | Config, Database (pgvector), Logging, Errors, LLM, Health |
| `hermes-agent-framework` | Config, Logging, Redis, Errors, LLM, Clients, Health |
| `ai-support-simulator` | Config, Logging, Errors, LLM, Clients |
| `github-issue-pr-agent` | Config, Logging, Errors, Clients |
| `personal-knowledge-base-os` | Config, Database (pgvector), Logging, Redis, Errors, LLM, Health |
| `real-time-analytics-stack` | Config, Database, Logging, Redis, Errors, Health, Clients |
| `game-systems-sandbox` | Config, Logging, Errors |

## Related Documentation

- [Architecture](docs/architecture.md) — Module dependency diagram and data flow
- [Design Decisions](docs/design-decisions.md) — ADRs for technology choices
- [Failure Modes](docs/failure-modes.md) — What breaks when shared-core has bugs
- [Roadmap](docs/roadmap.md) — Planned improvements
- [Security](docs/security.md) — Secrets handling and trust boundaries
- [Implementation Plan](docs/implementation_plan.md) — Technical implementation details
