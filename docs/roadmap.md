# Roadmap — shared-core

## Phase 0: MVP (Completed)

The initial `shared-core` v0.1.0 provides a functional library with five core modules:

- [x] **`BaseAppConfig`** — Pydantic v2 `BaseSettings` with `.env` loading, database/Redis URLs, API keys, and `extra="ignore"` for safe subclassing
- [x] **`DatabaseManager`** — SQLAlchemy 2.0 engine with `pool_pre_ping=True`, session generator, shared `Base`, `UUIDMixin`, `TimestampMixin`, and `BaseRepository`
- [x] **`setup_logging`** — Loguru structured logging with service tagging, colorization, correlation ID propagation, and `RequestLoggingMiddleware`
- [x] **`BaseApplicationError` hierarchy** — 10 exception classes with `.message`, `.code`, `.status_code` and ready-to-use FastAPI exception handler
- [x] **`RedisManager`** — Lazy Redis client with `ping()` health check, `@cache` decorator (sync+async), and `RedisLock` distributed lock

All five modules are importable and used by downstream projects. **25 unit tests** across 14 test files verify all modules. No CI pipeline exists yet.

---

## Phase 1: Display-Ready

### Testing (Complete)

- [x] Add `tests/` directory with pytest test suite
- [x] Unit tests for `BaseAppConfig` — default values, `.env` override, subclassing, `extra="ignore"` behavior
- [x] Unit tests for `DatabaseManager` — engine creation, session generator lifecycle (using SQLite in-memory)
- [x] Unit tests for error hierarchy — exception attributes, `ExternalAPIError` message formatting, all 10 error types
- [x] Unit tests for `setup_logging` — verify handler count, log level, service name injection
- [x] Unit tests for `RequestLoggingMiddleware` — correlation ID auto-generation and custom header forwarding
- [x] Unit tests for `RedisManager` — lazy init behavior, `ping()` return values (mocked Redis)
- [x] Unit tests for `@cache` decorator — sync and async (using `MockRedisClient`)
- [x] Unit tests for `RedisLock` — sync and async acquire/release/contention
- [x] Unit tests for `check_health` — healthy and degraded paths via mocks
- [x] Unit tests for `LLMClientFactory` — cost estimation, mock generation
- [x] Unit tests for `BaseHTTPClient` — GET with respx mock, 500 retry logic
- [x] Unit tests for `create_celery_app` — bootstrap with mocked celery module
- [x] Unit tests for `MockDatabase` and `MockRedisClient` — in-memory helpers
- [x] Add `conftest.py` with shared fixtures (`mock_db`, `mock_redis`, `app_config`)

### Health Check Utilities (Complete)

- [x] `shared_core.health` module with `check_health()` function
- [x] Database check — runs `SELECT 1` against PostgreSQL, returns per-dependency status
- [x] Redis check — wraps `ping()` with error handling
- [x] Standardized response format: `{"status": "healthy"|"degraded", "service": ..., "dependencies": {...}}`

### FastAPI Integration (Complete)

- [x] `application_error_handler` in `errors.py` — returns consistent JSON error responses for all `BaseApplicationError` subclasses
- [x] `RequestLoggingMiddleware` in `logging.py` — generates and propagates `X-Correlation-ID` headers, logs method/path/status/duration per request
- [x] `correlation_id_var` contextvar for manual correlation ID propagation

### Configuration Hardening

- [x] Use `SecretStr` for `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN` to prevent accidental serialization
- [x] Add `validate_config()` class method that returns a list of issues instead of raising
- [x] Add connection pool parameters to `BaseAppConfig`: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`

### HTTP Client (Complete)

- [x] `shared_core.clients` module with `BaseHTTPClient`
- [x] Async httpx client with exponential backoff retry on 5xx errors
- [x] Correlation ID forwarding via `correlation_id_var`
- [x] Convenience methods: `get`, `post`, `put`, `delete`

### LLM Integration (Complete)

- [x] `shared_core.llm` module with `LLMClientFactory`, `LLMResponse`, `estimate_llm_cost()`
- [x] Dynamic OpenAI/Anthropic imports (optional dependencies)
- [x] Standardized `LLMResponse` Pydantic model with token counts, latency, and cost
- [x] `generate_mock()` for fast unit testing without API calls
- [x] Static cost rate table for 4 models

### Task Queue (Complete)

- [x] `shared_core.tasks` module with `create_celery_app()`
- [x] Dynamic Celery import (optional dependency)
- [x] Signal-based Loguru logging on task prerun, postrun, and failure events
- [x] JSON serialization and time limit configuration

### Testing Harnesses (Complete)

- [x] `shared_core.testing` module with `MockDatabase` and `MockRedisClient`
- [x] `MockDatabase` — in-memory SQLite with `Base.metadata.create_all()` pre-run
- [x] `MockRedisClient` — full mock with `get`, `set` (ex/px/nx), `setex`, `delete`, `eval`, TTL

---

## Phase 2: Advanced Features

Stretch goals that improve the library beyond the display-ready baseline:

### Async Database Support

- [x] Add `AsyncDatabaseManager` using SQLAlchemy `AsyncSession` and `asyncpg` driver
- [x] Maintain backward compatibility — keep synchronous `DatabaseManager` alongside async version
- [x] Provide `get_session()` async generator for FastAPI `Depends()`
- [x] Add `close()` for explicit engine disposal

### Metrics and Observability

- [x] Add `shared_core.metrics` module with Prometheus client integration
- [x] Pre-defined metrics: HTTP request counter, request duration histogram, DB connections gauge, error counter
- [x] `MetricsMiddleware` for FastAPI that auto-instruments all endpoints
- [x] `metrics_endpoint()` factory function for Prometheus scrape endpoints
- [x] Dynamic import of `prometheus_client` — keeps it optional

### Enhanced Redis Utilities

- [x] Add `RedisManager.close()` for clean shutdown
- [x] Add `RedisManager.connect()` with connection retry and exponential backoff
- [x] Distributed lock utility via `RedisLock` (sync + async, Lua atomic release)
- [x] Cache decorator `@cache` with MD5 key hashing, JSON serialization, sync + async support

### CI Pipeline

- [x] Add `.github/workflows/ci.yml` with `ruff check`, `ruff format --check`, `pyright`, `pytest`
- [x] Python version matrix: 3.10, 3.11, 3.12
- [x] Self-contained install — no sibling path dependency for shared-core's own CI

### Documentation

- [x] Add API documentation generation with `mkdocs` + `mkdocs-material` + `mkdocstrings`
- [x] `docs/api/` stubs for all 11 source modules
- [x] `make docs` target for building documentation
- [x] Comprehensive README covering all modules
- [x] Updated architecture, design decisions, failure modes, security docs
- [x] Cross-platform `make clean` target (Python-based, works on Windows and Linux)

---

## Phase 3: Complete

All planned features are implemented. The library now provides:

| Module | Key Classes/Functions | Tests |
|--------|----------------------|-------|
| `config.py` | `BaseAppConfig`, `validate_config()` | 7 |
| `database.py` | `DatabaseManager`, `AsyncDatabaseManager`, `Base`, `UUIDMixin`, `TimestampMixin`, `BaseRepository` | 4 |
| `errors.py` | 10 exception classes, `application_error_handler` | 4 |
| `logging.py` | `setup_logging()`, `RequestLoggingMiddleware`, `correlation_id_var` | 3 |
| `redis.py` | `RedisManager`, `@cache`, `RedisLock` | 8 |
| `health.py` | `check_health()` | 2 |
| `clients.py` | `BaseHTTPClient` | 2 |
| `llm.py` | `LLMClientFactory`, `LLMResponse`, `estimate_llm_cost()` | 2 |
| `tasks.py` | `create_celery_app()` | 1 |
| `metrics.py` | `MetricsRegistry`, `MetricsMiddleware`, `metrics_endpoint()` | 2 |
| `testing.py` | `MockDatabase`, `MockRedisClient` | 2 |

**Total: 11 source modules, 37+ unit tests, CI pipeline, API documentation generation**

---

## Intentionally Not Building

These are out of scope for `shared-core` and will not be implemented:

- **ORM model definitions** — each project defines its own models; `shared-core` only provides `Base`
- **Authentication/authorization** — this is project-specific; `shared-core` does not implement auth
- **API routing** — no FastAPI routes; this is a library, not a service
- **Migration tooling** — Alembic setup is project-specific; `shared-core` only provides `create_tables()`
- **Multi-database support** — single `Base` / single `DatabaseManager` pattern; projects needing multiple databases extend it themselves
- **Message queue abstraction** — Celery is a project-level dependency, not a shared-core concern
- **Service discovery** — out of scope for a local-development showcase portfolio
- **Rate limiting** — project-specific; would couple the library to specific API patterns
- **Log aggregation/Sentry integration** — project-level concern; projects configure their own sinks
