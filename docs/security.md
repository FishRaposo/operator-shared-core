# Security Boundaries & Rules - Shared Core

This document defines the security parameters and boundaries of the `shared-core` library. Because `shared-core` is a shared package rather than a deployable service, its security focuses on secure code patterns, credential handling, and logging prevention.

---

## 1. Secrets & Credentials Handling

- **Zero Secret Storage**: The `shared-core` library MUST NOT contain any default api keys, passwords, or database credentials.
- **Pydantic Settings**: All configuration is loaded dynamically via `BaseAppConfig` utilizing Pydantic Settings. Values are read from environment variables, avoiding static config files.
- **Strict Exception Suppression**: Database connection errors and Redis connection failures must be caught and logged cleanly. Raw exception tracebacks containing connection strings (which may contain inline passwords) must be filtered or stripped of credentials before writing to logs.

---

## 2. Database Connection Security (`DatabaseManager`)

- **SSL Configuration**: The `DatabaseManager` is designed to support connection encryption. When deployed to staging or production, the database connection URL must include SSL parameters (e.g., `sslmode=require`).
- **Connection Pools**: Pool size and max overflow limits are managed strictly via configuration to prevent connection exhaustion attacks on the database server.
- **Query Parameterization**: While `shared-core` uses SQLAlchemy ORM which parameterizes queries by default, any raw SQL queries executed through the engine must utilize parameterized binds to eliminate SQL injection vulnerabilities.

---

## 3. Redis Security (`RedisManager`)

- **Authentication**: The `RedisManager` expects Redis connection strings containing authorization credentials in environments where Redis access is gated.
- **Connection Protection**: Lazy evaluation of the Redis client via properties prevents initialization errors on start, isolating downstream code from failing connection processes.

---

## 4. Structured Logging & PII Prevention (`setup_logging`)

- **Loguru Configuration**: Logs are structured in JSON format for production ingest.
- **Credential Masking**: Logging helpers must not output dump requests containing Authorization headers, Bearer tokens, or password fields.
- **Level Constraints**: Production deployments must set the log level to `INFO` or `WARNING` to prevent debug traces from outputting sensitive memory objects.

---

## 5. API Key Handling in LLMClientFactory

- `LLMClientFactory.__init__` receives API keys (`openai_api_key`, `anthropic_api_key`) and stores them in memory as plain strings (after unwrapping `SecretStr` if applicable).
- Keys are passed directly to SDK client constructors (`openai.OpenAI`, `anthropic.Anthropic`) and never logged, serialized, or transmitted outside the SDK's API calls.
- `LLMClientFactory` does not persist keys to disk, environment, or any external store.
- The `SecretStr` type in `BaseAppConfig` prevents accidental serialization of API keys via `model_dump()` or JSON encoding, but once unwrapped into the factory the keys are in-memory strings.

## 6. HTTP Client Request Security

- `BaseHTTPClient` does **not** log request bodies, headers, or query parameters. Only method, URL, attempt count, and response status are logged.
- The `X-Correlation-ID` header is automatically forwarded from the current context (`correlation_id_var`), but its value is a UUID — no sensitive information is embedded.
- Authorization headers and API keys must be passed by the downstream caller in the `headers` parameter — `BaseHTTPClient` does not auto-attach credentials.
- Downstream projects are responsible for not logging sensitive headers when calling `BaseHTTPClient` methods.

## 7. Metrics Endpoint Exposure

- `metrics_endpoint()` returns a FastAPI endpoint that exposes Prometheus metrics in plain text. This endpoint aggregates counters and histograms — it does not expose request bodies, headers, or any PII.
- Downstream projects should protect the `/metrics` endpoint from public access (e.g., internal network only, or basic auth) to prevent information disclosure about request patterns.

## 8. Editable Installation Security

- Since `shared-core` is installed in development mode (`pip install -e ../shared-core`), the sibling dependency relies on local directory structure. Ensure that user permissions on the development host restrict write access to the `shared-core` directory to prevent unauthorized alterations that could propagate across all active showcase projects.
