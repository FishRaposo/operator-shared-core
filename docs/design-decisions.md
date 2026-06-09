# Design Decisions — shared-core

## ADR-001: Centralized Shared Library Instead of Copy-Paste

### Context

The showcase portfolio contains 10+ Python projects that all need configuration loading, database connections, structured logging, error handling, and Redis access. The options were: (a) copy infrastructure code into each project, (b) publish a private PyPI package, or (c) maintain a shared library installed via editable local path.

### Options

1. **Copy-paste** — Each project gets its own `config.py`, `database.py`, etc.
2. **Private PyPI package** — Publish `shared-core` to a private index and pin versions
3. **Editable local install** — `pip install -e ../shared-core` from sibling directory

### Choice

**Editable local install** via `pip install -e ../shared-core`.

### Tradeoff

- ✅ Changes propagate instantly to all projects during development — no publish/install cycle
- ✅ No private PyPI infrastructure to maintain (no Artifactory, no GitHub Packages config)
- ✅ Standard Python packaging (`pyproject.toml` + `setuptools`) — no custom tooling
- ❌ Assumes a specific filesystem layout (`../shared-core` relative to each project)
- ❌ Breaks in isolated CI environments where only one repo is checked out
- ❌ No version pinning — a breaking change in `shared-core` immediately affects all projects

This is appropriate for a showcase/portfolio context where all repos are developed together. For production multi-team environments, the private PyPI approach would be better.

---

## ADR-002: Pydantic v2 BaseSettings for Configuration

### Context

Every project needs to load configuration from environment variables and `.env` files. The configuration must be typed, validated at startup, and extensible by downstream projects.

### Options

1. **`os.environ` + manual parsing** — Simple but no validation, no type safety
2. **`python-dotenv` + dataclasses** — Loads `.env` files but requires manual type coercion
3. **`pydantic-settings.BaseSettings`** — Automatic `.env` loading, Pydantic validation, type coercion, IDE autocomplete

### Choice

**Pydantic v2 `BaseSettings`** via `pydantic-settings ≥2.0.0`.

### Tradeoff

- ✅ Automatic type validation at instantiation — `DATABASE_URL` must be a string, `DEBUG` must be a bool
- ✅ `.env` file support built-in via `SettingsConfigDict(env_file=".env")`
- ✅ Downstream projects subclass `BaseAppConfig` and add fields — Pydantic handles the rest
- ✅ `extra="ignore"` means a shared `.env` file can contain vars for multiple projects without errors
- ❌ Adds `pydantic` and `pydantic-settings` as hard dependencies (though most projects already use Pydantic for API models)
- ❌ Cannot do dynamic config reloading — config is read once at import/instantiation time

---

## ADR-003: SQLAlchemy 2.0 with Synchronous Sessions

### Context

All database-backed projects use PostgreSQL. The library needs to provide engine creation, session management, and a shared ORM base class. Some projects (like `rag-evaluation-lab` and `personal-knowledge-base-os`) also use pgvector for vector similarity search.

### Options

1. **Raw `psycopg` connections** — Maximum control, no ORM overhead
2. **SQLAlchemy 2.0 synchronous** — Full ORM, session management, migration support
3. **SQLAlchemy 2.0 async** — `AsyncSession` with `asyncpg` driver
4. **SQLModel** — Combines SQLAlchemy + Pydantic, but less mature

### Choice

**SQLAlchemy 2.0 with synchronous sessions** and `psycopg` driver (specified via `postgresql+psycopg://` in `DATABASE_URL`).

### Tradeoff

- ✅ Mature, well-documented, widely understood ORM with excellent tooling
- ✅ `pool_pre_ping=True` provides automatic stale-connection detection
- ✅ `declarative_base()` gives downstream projects a shared base for ORM models
- ✅ `get_session()` generator pattern works with FastAPI `Depends()` and plain Python
- ❌ Synchronous only — projects needing async database access must extend or replace `DatabaseManager`
- ❌ Single `Base` instance means all models share one metadata registry (conflicts possible with multi-database setups)
- ❌ No built-in migration support — projects must add Alembic separately

The synchronous choice was deliberate: it keeps the shared library simple and avoids forcing async patterns on projects that don't need them. Projects requiring async can create their own `AsyncDatabaseManager`.

---

## ADR-004: Loguru Over stdlib logging

### Context

Every project needs structured, readable logging. The Python standard library `logging` module requires significant boilerplate for structured output, colorization, and service tagging.

### Options

1. **`logging` (stdlib)** — Universal, zero dependencies, but verbose setup
2. **`structlog`** — Structured logging with processors, good for JSON output
3. **`loguru`** — Zero-config structured logging with colorization, exception formatting, and context injection

### Choice

**Loguru** via `loguru ≥0.7.0`.

### Tradeoff

- ✅ Single function call (`setup_logging`) configures everything — no handlers, formatters, or filter boilerplate
- ✅ Built-in colorization, service tagging via `extra`, and rich exception tracebacks (`backtrace=True`, `diagnose=True`)
- ✅ `logger.remove()` + `logger.add()` pattern makes setup idempotent — safe to call multiple times
- ✅ `logger.configure(extra={"service": service_name})` injects service identity into every log line
- ❌ Non-standard — developers familiar with stdlib `logging` must learn Loguru's API
- ❌ Harder to integrate with libraries that use stdlib logging (requires `InterceptHandler`)
- ❌ Loguru's global state (`logger` is a module-level singleton) can cause issues if multiple libraries try to configure it

For a showcase portfolio where readability and demo appeal matter, Loguru's colorized output is a significant advantage over stdlib logging's default format.

---

## ADR-005: Typed Error Hierarchy with HTTP Semantics

### Context

All projects use FastAPI and need consistent error responses. Without a shared error structure, each project would define its own exception classes with incompatible formats, making it impossible to write reusable exception handlers.

### Options

1. **Raise `HTTPException` directly** — FastAPI-native but couples business logic to HTTP
2. **Plain exceptions + per-project handlers** — No coupling but no consistency
3. **Shared exception hierarchy with HTTP metadata** — Business exceptions carry enough info for HTTP mapping

### Choice

**Shared `BaseApplicationError` hierarchy** where each exception carries `.message`, `.code`, and `.status_code`.

### Tradeoff

- ✅ Downstream projects register a single exception handler for `BaseApplicationError` that works for all error types
- ✅ Business logic raises domain-specific exceptions (`DatabaseError`, `ExternalAPIError`) without importing FastAPI
- ✅ `ExternalAPIError` includes a `provider` field for identifying which external service failed
- ✅ Consistent JSON error response format across all projects: `{"code": "...", "message": "..."}`
- ❌ HTTP status codes are baked into exception classes — less flexible for non-HTTP contexts (CLI tools, background workers)
- ❌ `ValidationError` name collides with `pydantic.ValidationError` — downstream code must use qualified imports

---

## ADR-006: Lazy Redis Client Initialization

### Context

Not all projects use Redis, and even those that do may not need it at import time. Eagerly connecting to Redis at `RedisManager.__init__` would cause failures in projects that import `shared_core` but don't have Redis running.

### Options

1. **Eager connection in `__init__`** — Fail fast, but breaks projects that don't need Redis
2. **Lazy property** — Connect on first `.client` access
3. **Explicit `.connect()` method** — Most control, but requires manual lifecycle management

### Choice

**Lazy property** — `RedisManager._client` is `None` until first `.client` access.

### Tradeoff

- ✅ Projects can import and instantiate `RedisManager` without a running Redis server
- ✅ `ping()` gracefully returns `False` instead of raising — safe for health check endpoints
- ✅ No explicit lifecycle management needed (no `.connect()` / `.disconnect()` calls)
- ❌ Connection errors are deferred to first use, which may be harder to debug than a startup failure
- ❌ No connection pooling configuration exposed — uses `redis-py` defaults
- ❌ No explicit cleanup — the connection is never explicitly closed (relies on garbage collection)

---

## ADR-007: Simple Health Check Function Over a Class Hierarchy

### Context

Downstream projects need a standardized health check that queries their dependencies. The options were: (a) a `HealthChecker` class with pluggable checkers, (b) a simple function, (c) each project writes its own.

### Options

1. **`HealthChecker` class** with registered checkers and configurable thresholds
2. **Simple `check_health()` function** that runs fixed checks and returns a dict
3. **Per-project health checks** — no shared code

### Choice

**Simple `check_health(db_manager, redis_manager, service_name) -> dict` function.**

### Tradeoff

- ✅ Zero configuration — downstream projects call one function in their `/healthz` endpoint
- ✅ Returns standardized `{"status", "service", "dependencies"}` format across all projects
- ✅ Never raises — catches all exceptions internally, returns `"degraded"` with per-dependency status
- ✅ Single responsibility — checks database and Redis, the two dependencies every project has
- ❌ Not extensible — projects can't add custom health checks without modifying shared-core
- ❌ Only covers DB + Redis — doesn't check external APIs or Celery workers
- ❌ No latency measurement in the response — just "online"/"offline"

The function approach was chosen because health checks are typically simple (ping DB, ping Redis) and a class hierarchy would add complexity without proportional benefit for a showcase portfolio. Projects needing additional checks can wrap `check_health()` and add their own.

---

## ADR-008: HTTP Client with Exponential Backoff Retry

### Context

Several projects need to call external HTTP APIs (GitHub, LLM providers, webhooks). Without a shared HTTP client, each project would implement its own retry logic, timeout handling, and correlation ID propagation.

### Options

1. **`requests` library** — Synchronous, well-known, but blocking
2. **`httpx` synchronous** — Modern API, but still blocking
3. **`httpx.AsyncClient`** — Async, same API as `httpx`, supports connection pooling

### Choice

**`httpx.AsyncClient`** with exponential backoff retry on 5xx errors, correlation ID forwarding, and convenience methods.

### Tradeoff

- ✅ Async-first — matches FastAPI's async handler pattern, no thread pool needed
- ✅ Exponential backoff (`sleep_time = backoff_factor * 2^(attempt-1)`) prevents thundering herd on transient failures
- ✅ Correlation ID propagation — automatically reads `correlation_id_var` contextvar
- ✅ `raise_for_status()` on non-5xx responses — 4xx errors fail fast (no retry), 5xx errors retry
- ✅ Convenience methods (`get`, `post`, `put`, `delete`) wrap the retry logic
- ❌ No circuit breaker — repeated failures to the same host aren't remembered across calls
- ❌ No request body/header logging — debugging failed requests requires downstream logging
- ❌ httpx is a hard dependency — but most FastAPI projects already use it for `TestClient`

---

## ADR-009: LLM Client Factory with Dynamic Imports

### Context

Several projects use LLMs (OpenAI, Anthropic) for text generation. Adding `openai` and `anthropic` as hard dependencies would force every project to install both SDKs, even if they only use one provider (or none).

### Options

1. **Hard dependencies** — add `openai` and `anthropic` to `pyproject.toml`
2. **Separate optional packages** — `shared-core[openai]`, `shared-core[anthropic]`
3. **Dynamic imports** — import at call time, raise `ImportError` with install instructions

### Choice

**Dynamic imports** with clear `ImportError` messages telling the developer which package to install.

### Tradeoff

- ✅ Zero-cost for projects that don't use LLMs — no unused SDKs installed
- ✅ Clear error messages — `"openai module is not installed. Install it via 'pip install openai'"`
- ✅ `generate_mock()` provides a fast in-memory alternative for unit tests
- ✅ Standardized `LLMResponse` Pydantic model ensures consistent output format across providers
- ✅ Static cost table (`MODEL_COSTS`) provides cost estimation without API calls
- ❌ No type checking or IDE autocomplete for the LLM SDKs (they're `Any` typed at import boundary)
- ❌ Slightly slower first call due to import overhead
- ❌ Version coupling — no pinning of openai/anthropic SDK versions; downstream projects manage that

The factory pattern with dynamic imports follows the same approach as `create_celery_app()` — keep `shared-core` lightweight and let downstream projects opt into heavier dependencies.

---

## ADR-010: Testing Harnesses in shared-core

### Context

Every downstream project needs to test code that interacts with databases and Redis. Running real PostgreSQL and Redis in CI is slow and complex. Per-project mocks would duplicate effort.

### Options

1. **Docker-based testing** — run real Postgres/Redis in CI via Docker Compose
2. **Per-project mocks** — each project writes its own `MockDatabase` and `MockRedisClient`
3. **Shared testing harnesses** — provide `MockDatabase` and `MockRedisClient` in `shared-core`

### Choice

**Shared `MockDatabase` and `MockRedisClient`** in `shared_core.testing`, importable by all downstream projects.

### Tradeoff

- ✅ Zero-infrastructure unit tests — no Docker required, tests run in milliseconds
- ✅ `MockDatabase` uses SQLite in-memory with `Base.metadata.create_all()` — same schema as production, different dialect
- ✅ `MockRedisClient` supports `get`, `set` (with `ex`/`px`/`nx`), `setex`, `delete`, `eval` (Lua scripts), and TTL expiration
- ✅ Same generator-based `get_session()` interface as `DatabaseManager` — tests mirror production code
- ✅ Single source of truth — improvements to mocks benefit all projects
- ❌ SQLite ≠ PostgreSQL — dialect differences (e.g., JSON columns, pgvector) may hide bugs
- ❌ Schema ordering — downstream projects must register models on `Base` before instantiating `MockDatabase`
- ❌ No Redis pub/sub mock — only key-value operations

The shared harness approach was chosen because it enables fast, isolated unit tests across all 10+ projects. Projects needing PostgreSQL-specific tests (e.g., pgvector queries) should add Docker-based integration tests separately.

---

## ADR-011: Celery Bootstrap as a Utility Function

### Context

The `async-workflow-engine` and potentially other projects need Celery for background task processing. Celery requires boilerplate configuration (serialization format, timezone, signal handlers).

### Options

1. **Let each project configure Celery manually** — full control, more boilerplate
2. **`CeleryManager` class** — full lifecycle management (start, stop, health check)
3. **`create_celery_app()` utility function** — bootstrap with sensible defaults

### Choice

**`create_celery_app(service_name, broker_url, backend_url) -> Celery`** factory function with signal-based logging.

### Tradeoff

- ✅ Single function call replaces ~15 lines of Celery boilerplate
- ✅ JSON serialization, UTC timezone, task time limits (3600s) pre-configured
- ✅ Signal handlers (prerun, postrun, failure) automatically log task lifecycle via Loguru
- ✅ Dynamic import keeps `celery` optional — projects that don't use Celery don't install it
- ❌ Not a full lifecycle manager — no worker start/stop, no health check, no task routing configuration
- ❌ `task_time_limit` of 1 hour is a hard default — projects with longer tasks must override
- ❌ Signal handlers are always installed — projects can't opt out of automatic logging

The utility function approach provides 80% of the value (standardized config + logging) with 20% of the complexity of a full manager class. Projects needing more control can still configure Celery manually.
