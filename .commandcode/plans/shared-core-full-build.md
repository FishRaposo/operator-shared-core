# Implementation Plan: shared-core Full Build

## Current State

All 11 source modules and 25 unit tests are implemented. The gaps are:
- **Docs are stale** — README, architecture.md, and roadmap.md reference only 5 original modules and claim "no tests exist"
- **Phase 1 config hardening** — `SecretStr`, `validate_config()`, pool params not done
- **No conftest.py** — tests lack shared fixtures
- **No CI/CD** — no `.github/workflows/` directory
- **Phase 2 features** — AsyncDatabaseManager, metrics module, Redis retry/close, API docs generation

## Implementation Waves

---

### Wave 1: Documentation — Bring Docs in Sync with Code

All docs are in `shared-core/docs/`. Each needs targeted updates.

#### 1A. README.md (`shared-core/README.md`)

Full rewrite needed. Key changes:
- **What It Demonstrates** section: Add all new capabilities (HTTP client retries, LLM cost estimation, Celery bootstrap, health checks, distributed locks, `@cache` decorator, testing harnesses)
- **Module Reference** table: Add all 6 new modules — `shared_core.health`, `shared_core.clients`, `shared_core.llm`, `shared_core.tasks`, `shared_core.testing`, plus expanded error classes (`NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`, `ExternalServiceError`)
- **Project Structure** tree: Update to show all 11 source files
- **Dependencies table**: Add `httpx>=0.24.0` (already in pyproject.toml but missing from README)
- **Consumer Projects table**: Update to reflect new modules (e.g., `async-workflow-engine` now uses `health`, `clients`; `hermes-agent-framework` uses `llm`, `clients`)
- **Known Limitations**: Strike through items that are now resolved ("No unit tests" → "25 unit tests across 14 files", "No health check aggregator" → "check_health() in health.py", "No CI pipeline" → until Wave 4), add new limitations if any
- **Badge row**: Add badge for coverage/passing tests
- **Make targets table**: Update "No tests exist yet" → accurate test info

#### 1B. architecture.md (`shared-core/docs/architecture.md`)

- **Component Map** mermaid diagram: Expand from 5 to 10 modules. Add `clients.py`, `llm.py`, `tasks.py`, `health.py`, `testing.py`. Add external dependency boxes for external HTTP services, LLM APIs (OpenAI/Anthropic), Celery workers. Update downstream arrows to show which projects consume which new modules.
- **Module Responsibilities**: Add sections for each new module:
  - `health.py` — `check_health()` aggregating DB + Redis status
  - `clients.py` — `BaseHTTPClient` with retry logic and correlation ID propagation
  - `llm.py` — `LLMClientFactory` with dynamic OpenAI/Anthropic imports, cost estimation
  - `tasks.py` — `create_celery_app()` with signal-based logging
  - `testing.py` — `MockDatabase` (in-memory SQLite) and `MockRedisClient`
- Update **Failure Handling** table to include new modules
- Update **External Dependencies** table (add httpx, openai/anthropic as optional/dynamic)

#### 1C. roadmap.md (`shared-core/docs/roadmap.md`)

- **Phase 1** — Check off items that are done:
  - `[x]` Add `tests/` directory (25 tests exist)
  - `[x]` All individual test items
  - `[ ]` Add `conftest.py` — leave unchecked (done in Wave 2)
  - `[x]` `shared_core.health` module exists
  - `[x]` Standardize health check format
  - `[x]` `register_error_handlers` / middleware exists (`application_error_handler` + `RequestLoggingMiddleware`)
  - `[ ]` `SecretStr` — leave unchecked (done in Wave 2)
  - `[ ]` `validate_config()` — leave unchecked (done in Wave 2)
  - `[ ]` Pool parameters — leave unchecked (done in Wave 2)
- **Phase 2** — Keep all items; add: conftest.py, SecretStr migration, metrics module, API docs
- **Phase 3: Complete** — Add new section listing what's fully done

#### 1D. design-decisions.md (`shared-core/docs/design-decisions.md`)

Add new ADRs:
- **ADR-007: Health Check Design** — Why a simple function over a class, why `degraded` vs `unhealthy`, why only DB + Redis checks
- **ADR-008: HTTP Client with Retry** — Why httpx over requests, why exponential backoff, why correlation ID forwarding
- **ADR-009: LLM Client Factory Pattern** — Why dynamic imports for openai/anthropic, why cost estimation is included, why mock generation exists
- **ADR-010: Testing Harness Modules** — Why `MockDatabase` and `MockRedisClient` live in shared-core instead of per-project, why in-memory SQLite
- **ADR-011: Celery Bootstrap Utility** — Why `create_celery_app()` is in shared-core, why signal-based logging, why not a full Celery abstraction

#### 1E. failure-modes.md (`shared-core/docs/failure-modes.md`)

Add new failure modes:
- **FM-008: HTTP Client Retry Exhaustion** — Cause: external service down for all retry attempts
- **FM-009: LLM API Key Missing** — Cause: API key not set; mitigation: `generate_mock()` for testing
- **FM-010: Celery Broker Unavailable** — Cause: Redis not running; mitigation: signal logging catches failures
- **FM-011: MockDatabase Schema Mismatch** — Cause: downstream registers models after init

#### 1F. security.md (`shared-core/docs/security.md`)

Minor updates:
- Add section about `SecretStr` usage for API keys
- Add note about `BaseHTTPClient` not logging request bodies/headers by default
- Add note about `LLMClientFactory` handling API keys in memory

#### 1G. implementation_plan.md (`shared-core/docs/implementation_plan.md`)

- Update to reflect current reality (all milestones complete)
- Add new milestones for Phase 2 features
- Update file map to include any new files created in Waves 2-5

---

### Wave 2: Phase 1 Remaining Features — Configuration Hardening + Test Fixtures

#### 2A. SecretStr in `BaseAppConfig` (`src/shared_core/config.py`)

Change three fields from `Optional[str]` to `Optional[SecretStr]`:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GITHUB_TOKEN`

Update `LLMClientFactory.__init__` in `llm.py` to unwrap SecretStr automatically:
```python
self.openai_api_key = openai_api_key.get_secret_value() if hasattr(openai_api_key, 'get_secret_value') else openai_api_key
```

#### 2B. `validate_config()` class method (`src/shared_core/config.py`)

Add a `@classmethod` that returns a list of issues:
```python
@classmethod
def validate_config(cls, config_dict: dict | None = None) -> list[dict]:
```
Checks: missing DATABASE_URL, invalid LOG_LEVEL, LLM_TEMPERATURE out of range 0.0-2.0.

#### 2C. Connection Pool Parameters (`src/shared_core/config.py` + `database.py`)

Add to `BaseAppConfig`:
- `DB_POOL_SIZE: int = 5`
- `DB_MAX_OVERFLOW: int = 10`
- `DB_POOL_TIMEOUT: int = 30`

Update `DatabaseManager.__init__` to accept `pool_size`, `max_overflow`, `pool_timeout` params with matching defaults.

#### 2D. `conftest.py` (`tests/conftest.py`)

Shared fixtures: `mock_db`, `mock_redis`, `app_config`.

#### 2E. New Tests

- `tests/test_config_advanced.py`: SecretStr, validate_config, pool param defaults
- `tests/test_config_pool_params.py`: DatabaseManager pool param passthrough

---

### Wave 3: Phase 2 Features — Async DB, Metrics, Redis Enhancements, API Docs

#### 3A. AsyncDatabaseManager (`src/shared_core/database.py`)

New class alongside `DatabaseManager` using `AsyncSession`, `async_sessionmaker`, `create_async_engine`. Converts `postgresql+psycopg://` to `postgresql+asyncpg://`. Methods: `get_session()`, `create_tables()`, `close()`.

#### 3B. Metrics Module (`src/shared_core/metrics.py`)

New file with Prometheus integration using dynamic imports:
- `MetricsRegistry` — holds Counter, Histogram, Gauge for HTTP + errors
- `MetricsMiddleware` — auto-instruments FastAPI endpoints
- `metrics_endpoint()` — returns FastAPI endpoint for scrape

`prometheus_client` is NOT a hard dependency — follows the same dynamic import pattern as openai/anthropic/celery.

#### 3C. Redis Enhancements (`src/shared_core/redis.py`)

Add to `RedisManager`:
- `close()` — explicitly close client pool
- `connect(max_retries, backoff_factor)` — eager connect with exponential backoff retry

#### 3D. API Documentation Generation

- `mkdocs.yml` at project root with `mkdocs-material` + `mkdocstrings`
- Add `mkdocs`, `mkdocs-material`, `mkdocstrings[python]` to dev deps
- `docs/api/` with 11 stub `.md` files (one per module)
- `make docs` target: `mkdocs build`

#### 3E. New Tests

- `tests/test_database_async.py` — AsyncDatabaseManager with SQLite+aiosqlite
- `tests/test_metrics.py` — MetricsRegistry creation, counter, histogram
- `tests/test_redis_retry.py` — connect() retry behavior
- `tests/test_redis_close.py` — close() nullifies client

---

### Wave 4: CI/CD Pipeline

#### 4A. `.github/workflows/ci.yml`

GitHub Actions with: ruff check, ruff format --check, pyright src/, pytest -v. Python matrix: 3.10, 3.11, 3.12.

Self-contained install: `pip install -e .[dev]` — no sibling path dependency.

#### 4B. Update `pyproject.toml` dev dependencies

Add `respx>=0.20.0` and `pyright>=1.1.0` to dev deps.

#### 4C. Cross-Platform Makefile `clean`

Replace Windows cmd syntax with Python-based clean:
```makefile
clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('.ruff_cache', ignore_errors=True)"
```

---

### Wave 5: Final Polish

#### 5A. Version Bump

`0.1.0` → `1.0.0` in `__init__.py` and `pyproject.toml`.

#### 5B. Update AGENTS.md

Add: AsyncDatabaseManager, metrics, new dev deps (respx, pyright, mkdocs), `make docs` target.

#### 5C. Update `.env.example`

Add `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`.

#### 5D. Final Verification

`make lint && make format && make typecheck && make test && make demo`

---

## Files to Create (New)

| File | Wave |
|------|------|
| `tests/conftest.py` | 2 |
| `tests/test_config_advanced.py` | 2 |
| `tests/test_config_pool_params.py` | 2 |
| `src/shared_core/metrics.py` | 3 |
| `tests/test_database_async.py` | 3 |
| `tests/test_metrics.py` | 3 |
| `tests/test_redis_retry.py` | 3 |
| `tests/test_redis_close.py` | 3 |
| `mkdocs.yml` | 3 |
| `docs/api/` (11 stubs) | 3 |
| `.github/workflows/ci.yml` | 4 |

## Files to Modify (Existing)

| File | Wave | Changes |
|------|------|---------|
| `README.md` | 1 | Full rewrite — all modules, accurate stats, updated deps table |
| `docs/architecture.md` | 1 | Expanded mermaid diagram, new module sections |
| `docs/roadmap.md` | 1 | Check off done items, add Phase 2 items, add Phase 3 |
| `docs/design-decisions.md` | 1 | Add ADRs 007–011 |
| `docs/failure-modes.md` | 1 | Add FM-008 through FM-011 |
| `docs/security.md` | 1 | SecretStr, HTTP client, LLM key handling notes |
| `docs/implementation_plan.md` | 1 | Sync with reality, add Phase 2 milestones |
| `src/shared_core/config.py` | 2 | SecretStr, validate_config(), pool params |
| `src/shared_core/database.py` | 2+3 | Pool params in constructor, add AsyncDatabaseManager |
| `src/shared_core/llm.py` | 2 | Handle SecretStr unwrapping |
| `src/shared_core/redis.py` | 3 | Add close(), connect() with retry |
| `src/shared_core/__init__.py` | 5 | Bump version to 1.0.0 |
| `pyproject.toml` | 4+5 | Add respx, pyright, mkdocs deps; bump version |
| `Makefile` | 3+4 | Add docs target, cross-platform clean |
| `.env.example` | 5 | Add pool param fields |
| `AGENTS.md` | 5 | Add new modules, deps, commands |

## Verification Plan

After each wave:
```bash
make lint && make format && make typecheck && make test
```

After full build:
```bash
make demo   # Exercises config/logging/db/redis/errors/health
make docs   # Verifies mkdocs builds cleanly
```
