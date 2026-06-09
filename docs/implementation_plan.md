# Implementation Plan - Shared Core

This document details the step-by-step technical implementation plan and development milestones for **Shared Core** (Project 1).

---

## 1. Project Goal
`shared-core` is the foundational utility and infrastructure library for all microservices in the operator systems showcase. It standardizes configuration loading, database pools, logging formats, exception hierarchies, Redis client utilities (caching, locks), HTTP/LLM client gateways, task queue loaders, health checks, metrics, and in-memory testing harnesses.

---

## 2. Architecture & Component Map

The repository is structured as a standalone Python library exposed as a PEP 517 package:

### 2.1 File Map & Responsibilities
* **`src/shared_core/config.py`**: Configuration model parsing settings from `.env` files using Pydantic Settings. Includes `SecretStr` for API keys, `validate_config()` for pre-flight validation, and connection pool parameters.
* **`src/shared_core/database.py`**: SQLAlchemy engines (sync + async), base declarative class, UUID/Timestamp mixins, and generic CRUD repositories. `DatabaseManager` for sync, `AsyncDatabaseManager` for async with `asyncpg`.
* **`src/shared_core/errors.py`**: 10-exception hierarchy matching HTTP error states (400, 401, 403, 404, 409, 500, 502) and FastAPI exception handler.
* **`src/shared_core/logging.py`**: Structured Loguru layouts with correlation ID contextvar propagation and `RequestLoggingMiddleware` for FastAPI auto-instrumentation.
* **`src/shared_core/redis.py`**: Lazy Redis manager, `@cache` decorator (sync+async, MD5 hashing), `RedisLock` distributed lock (sync+async, Lua atomic release), `connect()` with retry, and `close()` for cleanup.
* **`src/shared_core/health.py`**: Health check indicators querying PostgreSQL and Redis, returning standardized `{status, service, dependencies}` responses.
* **`src/shared_core/clients.py`**: Outbound HTTP `AsyncClient` with exponential backoff retries on 5xx and correlation ID forwarding.
* **`src/shared_core/llm.py`**: OpenAI/Anthropic client factories with dynamic imports, standardized `LLMResponse`, token usage and USD cost estimation, and `generate_mock()` for testing.
* **`src/shared_core/tasks.py`**: Celery app builders registering Loguru hook handlers on prerun/postrun/failure execution signals.
* **`src/shared_core/metrics.py`**: Prometheus-compatible `MetricsRegistry` (Counter, Histogram, Gauge), `MetricsMiddleware` for FastAPI auto-instrumentation, and `metrics_endpoint()` factory. Dynamic import keeps `prometheus_client` optional.
* **`src/shared_core/testing.py`**: `MockDatabase` (in-memory SQLite) and `MockRedisClient` (full mock with TTL and NX semantics) for isolated unit testing.

---

## 3. Database Schema & Data Models

### 3.1 Data Schema
* No dedicated table migrations are managed within `shared-core`. Sibling services define their own tables inheriting from `shared_core.database.Base`.
* `shared-core` exposes `TimestampMixin` and `UUIDMixin` to unify primary key and timestamp configurations.
* `BaseRepository[T]` provides generic CRUD (get/list/create/update/delete) that downstream services can use directly or subclass.

### 3.2 Redis Storage & Caching Patterns
* Caching: `@cache` decorator writes JSON outputs with MD5-hashed argument keys under configurable prefixes. Supports both sync and async functions.
* Concurrency: `RedisLock` ensures atomic block locking via Lua script releases with configurable TTL and acquire timeout. Supports both `with` and `async with` context managers.
* Connection: Lazy initialization with optional eager `connect()` supporting exponential backoff retry. Explicit `close()` for clean pool shutdown.

---

## 4. Step-by-Step Implementation Sequence

The project development checklist is organized into milestones:

### Completed Milestones

- `[x]` **Milestone 1 (Design):** Plan base configuration variables, SQL database model mixins, and Loguru logging format layouts.
- `[x]` **Milestone 2 (Skeleton):** Initialize FastAPI exception handlers, SQLAlchemy configurations, and Redis managers.
- `[x]` **Milestone 3 (Core Loop):** Build robust logging middleware, `@cache` decorators, and distributed lock handlers.
- `[x]` **Milestone 4 (Reliability):** Implement HTTP Client retries, LLM client providers, and Celery task builders.
- `[x]` **Milestone 5 (Showcase):** Build runnable local demonstration script examples exercising all modules.
- `[x]` **Milestone 6 (Publish):** Expand unit test coverage across all features, verify type checking, and packaging.
- `[x]` **Milestone 7 (Config Hardening):** `SecretStr` for API keys, `validate_config()` pre-flight validation, connection pool parameters.
- `[x]` **Milestone 8 (Async Support):** `AsyncDatabaseManager` with SQLAlchemy `AsyncSession` and `asyncpg` driver.
- `[x]` **Milestone 9 (Observability):** `MetricsRegistry` and `MetricsMiddleware` with Prometheus integration.
- `[x]` **Milestone 10 (Documentation):** Comprehensive README, updated architecture/ADRs/failure-modes, API docs via mkdocs.
- `[x]` **Milestone 11 (CI/CD):** GitHub Actions pipeline with lint, format check, type check, and tests across Python 3.10–3.12.

---

## 5. Standard Makefile & Developer Commands

```bash
make install          # Set up virtual environment and local editable package
make dev              # Run the examples demonstration script
make test             # Run local pytest test suites
make lint             # Execute Ruff checks
make format           # Standardize style formatting
make typecheck        # Verify static types (Pyright)
make docs             # Build API documentation with mkdocs
make docker-up        # Spawn isolated local PostgreSQL and Redis service containers
make docker-down      # Teardown the isolated local containers stack
make demo             # Execute the runnable demo workflow
make clean            # Remove caches and temporary files (cross-platform Python)
```

---

## 6. Verification & Testing Plan

### 6.1 Automated Tests
* **Core Logic Verification**: 37+ unit tests under `tests/` verifying all 11 modules.
* **Type Safety & Style**: Run `make typecheck` and `make lint` as pipeline validation hooks.
* **Mock Environments**: Utilize `MockDatabase` and `MockRedisClient` to run test suites cleanly without requiring active local Docker containers.
* **Shared Fixtures**: `conftest.py` provides `mock_db`, `mock_redis`, and `app_config` fixtures for all test files.

### 6.2 Manual Verification
* Deploy local PostgreSQL and Redis containers with `make docker-up`.
* Execute the runnable script demo `make demo` and review Loguru stdout records.
* Build documentation with `make docs` and verify all module stubs generate cleanly.

### 6.3 CI Verification
* GitHub Actions runs on push/PR to `main` across Python 3.10, 3.11, 3.12.
* Steps: `ruff check`, `ruff format --check`, `pyright src/`, `pytest -v`.
* `shared-core` installs itself via `pip install -e .[dev]` — no sibling path dependency in its own CI.
