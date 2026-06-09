# Failure Modes — shared-core

Because `shared-core` is the foundation library for every project in the portfolio, bugs or misconfigurations here cascade to all downstream consumers. This document catalogs the known failure modes, their blast radius, and mitigation strategies.

---

## FM-001: Configuration Validation Failure at Startup

### Cause

A downstream project instantiates `BaseAppConfig` (or a subclass) but the `.env` file is missing, malformed, or contains values that fail Pydantic type validation. For example, `DEBUG=notabool` when `DEBUG` is typed as `bool`.

### Impact

**Total application failure.** The project cannot start. `pydantic.ValidationError` is raised during `BaseAppConfig()` instantiation, before any server or worker process begins.

### Detection

Immediate — the process crashes with a Pydantic validation traceback on startup.

### Mitigation

- All fields in `BaseAppConfig` have sensible defaults, so a missing `.env` file still produces a valid config
- `extra="ignore"` prevents unrecognized env vars from causing validation errors
- Downstream projects should catch `pydantic.ValidationError` at startup and log a human-readable message

### Future Fix

- Add a `validate_config()` class method that returns a list of issues instead of raising
- Add a `make check-env` target that validates `.env` without starting the application

---

## FM-002: Database Connection Failure

### Cause

`DatabaseManager` is initialized with an invalid or unreachable `DATABASE_URL`. The engine is created lazily by SQLAlchemy, so the failure doesn't occur at `__init__` time — it occurs on first query or `create_tables()` call.

### Impact

**Deferred crash.** The application starts successfully, but the first database operation raises `sqlalchemy.exc.OperationalError`. For FastAPI projects, this typically manifests as a 500 error on the first request that touches the database.

### Detection

- First database query fails with `OperationalError`
- `pool_pre_ping=True` will detect stale connections on subsequent requests, but cannot detect that the initial connection was never established

### Mitigation

- `pool_pre_ping=True` in `create_engine()` handles transient connection drops (PostgreSQL restart, network blip)
- Downstream projects should call `db.create_tables()` at startup, which will fail fast if the database is unreachable
- The `DatabaseError` exception class exists for downstream projects to wrap and handle SQLAlchemy errors

### Future Fix

- Add a `DatabaseManager.check_connectivity()` method that runs a `SELECT 1` query
- Add connection pool tuning parameters (`pool_size`, `max_overflow`, `pool_timeout`) to `BaseAppConfig`
- Add async database support via `AsyncSession` for projects that need it

---

## FM-003: Redis Unreachable on First Access

### Cause

`RedisManager` uses lazy client initialization. If Redis is not running when `.client` is first accessed (not when `RedisManager` is instantiated), `redis.ConnectionError` is raised.

### Impact

**Partial failure.** Only features that use Redis are affected. If Redis is used for caching, the application may fall back to uncached behavior (if the downstream project handles the exception). If Redis is used for Celery task queuing, all background job dispatch fails.

### Detection

- `RedisManager.ping()` returns `False` — this is the designed health check path
- Direct `.client` access raises `redis.ConnectionError`

### Mitigation

- `ping()` method catches `redis.RedisError` internally and returns `False` — safe for health check endpoints
- Downstream projects should check `redis_mgr.ping()` at startup and log a warning if Redis is unavailable
- Lazy initialization means the application can start even without Redis, deferring failure to first use

### Future Fix

- Add `RedisManager.check_connectivity()` that raises `ConfigurationError` if Redis is down
- Add connection retry logic with exponential backoff
- Add `RedisManager.close()` for clean shutdown

---

## FM-004: Shared `Base` Metadata Collision

### Cause

All downstream projects import `Base` from `shared_core.database` and register their ORM models against it. If two projects are loaded in the same Python process (unlikely but possible in test suites or monorepo tooling), their model definitions can collide on table names.

### Impact

**Silent data corruption or `InvalidRequestError`.** SQLAlchemy may raise an error about duplicate table names in the same `MetaData` registry, or silently overwrite one model's definition with another's.

### Detection

- `sqlalchemy.exc.InvalidRequestError` at import time when two models share a `__tablename__`
- Incorrect query results if tables are silently redefined

### Mitigation

- Each project runs in its own virtual environment and process, making collisions extremely unlikely in normal operation
- Projects should use distinctive, project-prefixed table names (e.g., `workflow_tasks` not just `tasks`)

### Future Fix

- Consider providing a `create_scoped_base()` factory that returns a new `declarative_base()` per project
- Document the table naming convention in the project template

---

## FM-005: Logging Reconfiguration Overwrites Previous Setup

### Cause

`setup_logging()` calls `logger.remove()` to clear all existing handlers before adding its own. If a downstream project or a third-party library has already configured Loguru handlers, they are silently removed.

### Impact

**Lost log output.** Any Loguru handlers configured before `setup_logging()` is called (e.g., file handlers, Sentry integration, or structured JSON handlers) are removed. Only the stdout handler from `setup_logging()` remains.

### Detection

- Difficult to detect — logs simply stop appearing in the expected destination
- Only noticeable if the project intentionally configured additional Loguru sinks before calling `setup_logging()`

### Mitigation

- Call `setup_logging()` first, before any other logging configuration
- If additional sinks are needed, add them after calling `setup_logging()`

### Future Fix

- Add an `additional_sinks` parameter to `setup_logging()` that configures extra outputs (file, JSON, Sentry)
- Add a `clear_existing: bool = True` parameter to optionally preserve existing handlers
- Consider returning the handler ID from `logger.add()` so callers can manage it

---

## FM-006: API Key Exposure via Config Object

### Cause

`BaseAppConfig` loads `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GITHUB_TOKEN` into plain string attributes. If the config object is logged, serialized, or exposed via a debug endpoint, these secrets are visible in cleartext.

### Impact

**Credential leak.** API keys could appear in log files, error tracebacks, debug responses, or serialized config dumps.

### Detection

- Code review — search for `config.OPENAI_API_KEY` in log statements or response bodies
- Secret scanning tools (e.g., `trufflehog`, GitHub secret scanning) on committed code

### Mitigation

- Pydantic's `model_dump()` includes all fields by default, but API keys are `Optional[str]` with `None` default — they are only present if explicitly set
- `.env` files are in `.gitignore` and never committed
- Loguru's `diagnose=True` can expose local variables in tracebacks — this is acceptable for development but must be disabled in production

### Future Fix

- Use Pydantic's `SecretStr` type for API key fields to prevent accidental serialization
- Add `model_config` with `json_schema_extra` to exclude sensitive fields from serialization
- Disable `diagnose=True` when `ENV != "development"`

---

## FM-007: Editable Install Path Breakage in CI

### Cause

All downstream projects install `shared-core` via `pip install -e ../shared-core`, which assumes the library exists at a specific relative filesystem path. In CI environments (GitHub Actions), only one repository is typically checked out at a time.

### Impact

**CI pipeline failure.** `make install` fails because `../shared-core` doesn't exist. No downstream project can be built or tested in isolation.

### Detection

Immediate — `pip install -e ../shared-core` fails with `FileNotFoundError`.

### Mitigation

- Currently, CI is not set up for any project — this is a known gap
- For local development, the standard workspace layout ensures the path exists

### Future Fix

- Publish `shared-core` to a private PyPI index (GitHub Packages or Artifactory)
- Use a monorepo checkout strategy in CI that clones both the project and `shared-core`
- Alternatively, use git submodules to embed `shared-core` in each project

---

## FM-008: HTTP Client Retry Exhaustion

### Cause

`BaseHTTPClient` retries failed requests up to `max_retries` times with exponential backoff. If the external service is persistently down, all retries are exhausted and the final `httpx.HTTPError` propagates to the caller.

### Impact

**Cascading failure.** The downstream project's request fails with an unhandled `httpx.HTTPError`. If the downstream code doesn't catch this, the FastAPI endpoint returns a 500 Internal Server Error with a raw traceback instead of a structured error response.

### Detection

- Log messages: `"HTTP Request failed after {attempt} attempts: {method} {url}"` from `BaseHTTPClient`
- Downstream error monitoring shows spikes in `httpx.HTTPError` or unhandled 500s

### Mitigation

- Downstream projects should catch `httpx.HTTPError` from `BaseHTTPClient` calls and re-raise as `ExternalAPIError` or `ExternalServiceError`
- `max_retries` defaults to 3 with 0.5s backoff factor — adjust per-endpoint based on SLA requirements
- 4xx errors fail fast (no retry) — avoids wasting retries on auth errors or bad requests

### Future Fix

- Add a circuit breaker pattern that stops retrying a failing host for a cooldown period
- Add configurable retry conditions (retry on specific status codes, not all 5xx)
- Add `BaseHTTPClient` request metrics exposed via `MetricsRegistry`

---

## FM-009: LLM API Key Missing or Invalid

### Cause

`LLMClientFactory.generate_openai()` or `generate_anthropic()` is called but the corresponding API key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) is `None` or invalid. The underlying SDK raises an authentication error.

### Impact

**Request failure.** The LLM generation call fails. If the downstream project's error handling is robust, it catches the exception and returns a structured error. If not, it propagates as an unhandled exception.

### Detection

- SDK-specific authentication errors (e.g., `openai.AuthenticationError`, `anthropic.AuthenticationError`)
- Downstream logs show API call failures with auth-related status codes (401)

### Mitigation

- Use `generate_mock()` for development and testing — no API key required, returns a fake response in ~50ms
- Downstream projects should validate API key presence at startup using `validate_config()`
- `LLMClientFactory.__init__` doesn't validate keys — it defers to the SDK's first API call
- `SecretStr` in `BaseAppConfig` prevents accidental key logging, but doesn't detect missing keys

### Future Fix

- Add `LLMClientFactory.validate_keys()` that pings each provider's auth endpoint
- Add configurable fallback chain (try OpenAI, fall back to Anthropic, fall back to mock)

---

## FM-010: Celery Broker Unavailable

### Cause

`create_celery_app()` is called and tasks are dispatched, but the Redis broker is not running or unreachable. Celery tasks cannot be queued or consumed.

### Impact

**Silent task loss.** Depending on the Celery configuration:
- If `task_acks_late=False` (default), tasks may be lost if the broker is unreachable at dispatch time
- If the broker becomes unreachable after tasks are queued, workers disconnect and tasks remain in the queue unprocessed
- Downstream features relying on async task completion stall indefinitely

### Detection

- `task_failure` signal handler in `create_celery_app()` logs failures — but only if the worker was able to receive the task
- Redis connectivity monitoring (via `RedisManager.ping()`) can detect broker issues
- Stuck tasks visible in Celery monitoring tools (Flower)

### Mitigation

- The signal handlers installed by `create_celery_app()` provide Loguru logging for every task lifecycle event
- Call `redis_mgr.ping()` at startup to verify broker connectivity before dispatching tasks
- Use `RedisManager.connect()` with retry for eager broker connection validation
- `task_track_started=True` provides visibility into task state

### Future Fix

- Add `send_task()` wrapper that catches broker connection errors and raises `ExternalServiceError`
- Add configurable retry on broker connection failure at task dispatch time
- Add Celery health check to `check_health()` (monitor broker connectivity and worker count)

---

## FM-011: MockDatabase Schema Timing Mismatch

### Cause

`MockDatabase.__init__()` calls `Base.metadata.create_all()` to create all registered tables. If a downstream test file registers ORM models on `Base` after `MockDatabase` is instantiated, those new tables won't exist in the SQLite in-memory database.

### Impact

**Confusing test failures.** `sqlalchemy.exc.OperationalError` with "no such table" when a test queries a model that was imported after `MockDatabase` was created. This is especially confusing because the model class exists and looks correct — only the backing table is missing.

### Detection

- `OperationalError: no such table: <tablename>` in test output
- Tests pass when run individually but fail when run as a suite (import order differs)

### Mitigation

- Import all models **before** instantiating `MockDatabase` — standard pattern is to create the mock in a fixture or `setUp` method
- Use `conftest.py` fixtures (`mock_db`) that create `MockDatabase` on first use, after all test modules are imported
- Call `Base.metadata.create_all(bind=mock_db.engine)` again after importing additional models if needed
- Document this behavior in `testing.py` docstring and project README

### Future Fix

- Add `MockDatabase.refresh_schema()` method that re-runs `create_all()` for late-registered models
- Consider a `reset_database()` fixture that drops and recreates all tables between tests for strict isolation
