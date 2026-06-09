# AGENTS.md — shared-core (Project 1)

## What This Is

`shared-core` is the core Python library (Project 1 in the portfolio) that provides the common infrastructure foundation for all microservices in the Operator Systems portfolio. It exposes 11 modules: configuration management, database connectivity (sync + async), Redis wrappers (caching, locks, retry), structured logging with correlation IDs, a 10-exception typed error hierarchy, health checks, async HTTP client with retry, LLM integration, Celery bootstrap, Prometheus metrics, and in-memory testing harnesses.

It is fully scaffolded as an independent project with its own local Docker Compose environment (Postgres/Redis), 45 unit tests, CI pipeline (GitHub Actions), API documentation generation (mkdocs), and runnable example demo.

## Commands

```bash
make install    # pip install -e .[dev] — installs library + dev tools
make test       # pytest — executes 45 unit tests
make lint       # ruff check . — linting checks
make format     # ruff format . — code formatting
make typecheck  # pyright — type verification
make docs       # mkdocs build — API documentation generation
make docker-up  # docker compose up -d — starts Postgres (with pgvector) and Redis
make docker-down# docker compose down — stops infrastructure
make demo       # python examples/run_demo.py — runs the example script
make clean      # Python shutil cleanup — cross-platform cache removal
```

## Entry Point & Demos

- **`examples/run_demo.py`**: A runnable demo executing Pydantic settings loading, logging outputs, SQLAlchemy sessions, Redis ping, exceptions, and `check_health` calculations.

## Source Modules

| File | Exports | Purpose |
|------|---------|---------|
| `src/shared_core/__init__.py` | `__version__` | Package marker, version `1.0.0` |
| `src/shared_core/config.py` | `BaseAppConfig`, `validate_config()` | Pydantic `BaseSettings` with `SecretStr` for API keys, connection pool params, pre-flight validation |
| `src/shared_core/database.py` | `DatabaseManager`, `AsyncDatabaseManager`, `Base`, `TimestampMixin`, `UUIDMixin`, `BaseRepository` | SQLAlchemy sync + async engines, declarative base, ORM mixins, generic CRUD repository |
| `src/shared_core/errors.py` | 10 exception classes + `application_error_handler` | Full HTTP error hierarchy (400–502) with FastAPI handler |
| `src/shared_core/logging.py` | `setup_logging`, `RequestLoggingMiddleware`, `correlation_id_var` | Loguru structured logging, correlation ID tracing, request logging middleware |
| `src/shared_core/redis.py` | `RedisManager`, `cache`, `RedisLock` | Lazy Redis client, `@cache` sync/async decorator, RedisLock, `connect()` retry, `close()` cleanup |
| `src/shared_core/health.py` | `check_health` | Reusable health indicators checking DB and Redis |
| `src/shared_core/clients.py` | `BaseHTTPClient` | Async httpx client with exponential backoff retry and correlation ID forwarding |
| `src/shared_core/llm.py` | `LLMClientFactory`, `LLMResponse`, `estimate_llm_cost` | Dynamic OpenAI/Anthropic clients, cost estimation, standardized LLMResponse, mock generation |
| `src/shared_core/tasks.py` | `create_celery_app` | Celery bootstrap with signal-based Loguru logging |
| `src/shared_core/metrics.py` | `MetricsRegistry`, `MetricsMiddleware`, `metrics_endpoint()` | Prometheus metrics with isolated CollectorRegistry, FastAPI middleware, scrape endpoint |
| `src/shared_core/testing.py` | `MockDatabase`, `MockRedisClient` | In-memory SQLite + Redis mocks for isolated unit testing |

## Docker Services

- **postgres**: pgvector/pgvector:pg16 on host port 5432
- **redis**: redis:7-alpine on host port 6379

## Layout

```
shared-core/
├── pyproject.toml              # Package metadata, dependencies
├── requirements.txt            # Locked pip requirements
├── Makefile                    # Standard commands (includes docs target)
├── docker-compose.yml          # Postgres + Redis container configurations
├── mkdocs.yml                  # API documentation generation config
├── pytest.ini                  # Pytest settings
├── ruff.toml                   # Ruff rules
├── pyrightconfig.json          # Pyright types configurations
├── .env.example                # Example environment keys (includes pool params)
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml              # CI pipeline (lint, format, typecheck, test on 3.10–3.12)
├── src/
│   └── shared_core/
│       ├── __init__.py         # __version__ = "1.0.0"
│       ├── config.py           # BaseAppConfig, validate_config()
│       ├── database.py         # DatabaseManager, AsyncDatabaseManager, Base, BaseRepository, mixins
│       ├── errors.py           # 10-exception hierarchy + FastAPI handler
│       ├── logging.py          # setup_logging(), RequestLoggingMiddleware
│       ├── redis.py            # RedisManager, @cache, RedisLock, connect(), close()
│       ├── health.py           # check_health()
│       ├── clients.py          # BaseHTTPClient
│       ├── llm.py              # LLMClientFactory, LLMResponse, estimate_llm_cost()
│       ├── tasks.py            # create_celery_app()
│       ├── metrics.py          # MetricsRegistry, MetricsMiddleware, metrics_endpoint()
│       └── testing.py          # MockDatabase, MockRedisClient
├── examples/
│   └── run_demo.py             # Runnable demo script
├── tests/                      # 45 unit tests across 18 test files
│   └── conftest.py             # Shared fixtures (mock_db, mock_redis, app_config)
├── docs/
│   ├── architecture.md         # System overview and component diagrams
│   ├── design-decisions.md     # Architecture Decision Records (ADRs 001–011)
│   ├── failure-modes.md        # Failure mode catalog (FM-001 through FM-011)
│   ├── roadmap.md              # Development phases and milestones
│   ├── security.md             # Security boundaries and rules
│   ├── implementation_plan.md  # Technical implementation details
│   └── api/                    # API reference stubs for mkdocs generation
├── README.md
└── AGENTS.md
```

## Current State

**Complete, tested library (Project 1).** All 12 source modules implemented. 45 unit tests passing. GitHub Actions CI configured (python 3.10–3.12). API documentation via mkdocs. Version 1.0.0.

## Key Dependencies

Declared in `pyproject.toml`:

- `pydantic-settings ≥2.0.0` — `.env` file loading for `BaseAppConfig`
- `pydantic ≥2.0.0` — data validation, `SecretStr`
- `sqlalchemy ≥2.0.0` — ORM, engine, sessions (sync + async)
- `pgvector ≥0.2.0` — vector column type for PostgreSQL
- `redis ≥5.0.0` — Redis client
- `loguru ≥0.7.0` — structured logging
- `httpx ≥0.24.0` — async HTTP client

Dev: `pytest ≥7.0.0`, `ruff ≥0.1.0`, `pyright ≥1.1.0`, `respx ≥0.20.0`, `mkdocs ≥1.5.0`, `mkdocs-material ≥9.0.0`, `mkdocstrings[python] ≥0.24.0`

Optional (dynamically imported): `openai`, `anthropic`, `celery`, `prometheus-client`

## Conventions

- `BaseAppConfig` reads `.env` via `SettingsConfigDict` — downstream projects subclass it and add their own fields
- `extra="ignore"` in config means unknown env vars don't cause errors — safe for shared `.env` files
- API keys use `SecretStr` — call `.get_secret_value()` to extract plaintext; `LLMClientFactory` unwraps automatically
- `validate_config()` returns a list of issues (field/message/severity) without raising — downstream projects call it at startup
- `DatabaseManager.get_session()` is a generator — use with `Depends()` in FastAPI or `next()` in scripts
- `AsyncDatabaseManager.get_session()` is an async generator — use with `async for` or FastAPI async `Depends()`
- Pool params are conditional — SQLite URLs skip `pool_size`/`max_overflow`/`pool_timeout` (not supported by SingletonThreadPool)
- `Base` from `database.py` is the single declarative base — ALL project ORM models inherit from it
- `BaseRepository` implements the standard generic CRUD pattern. Downstream services subclass it or use it directly by passing the model type.
- Error classes carry HTTP semantics (`status_code`, `code`) — downstream projects register FastAPI exception handlers against `BaseApplicationError`
- `RequestLoggingMiddleware` manages `correlation_id_var` and formats all records to contain the `correlation_id`.
- `@cache` hashes function arguments (sync/async) using stable MD5 keys.
- `RedisLock` supports sync (`with`) and async (`async with`) blocks and releases locks atomically via Lua scripts.
- `RedisManager.connect()` retries with exponential backoff; `close()` explicitly shuts down the pool.
- `LLMClientFactory` dynamically imports `openai` and `anthropic` client SDKs to keep dependency installation lightweight.
- `MetricsRegistry` uses its own `CollectorRegistry` to avoid metric name collisions when multiple instances exist.
- `MockDatabase` and `MockRedisClient` from `testing.py` must be used to keep microservice unit tests isolated (running without requiring active Docker containers).

## Impact of Changes

**Changes to shared-core affect all 10+ downstream projects.** Before modifying:

1. Check which modules are imported by downstream projects
2. Maintain backward compatibility — don't rename exports or change signatures
3. After modifying, verify at least one downstream project still passes `make test`
4. Update this AGENTS.md if modules are added/removed, signatures change, or dependencies change

## When to Update This AGENTS.md

- Modules added or removed from `src/shared_core/`
- Public API changes (new classes, renamed functions, changed signatures)
- Dependencies added or removed in `pyproject.toml`
- Install procedure changes
- State transitions (e.g., tests added, CI configured, version bump)
