# Operator Systems Template — Starter and Reference Guide

> **Documentation-only absorption.** This guide records reusable operating conventions from `operator-systems-template`; it does not add, copy, or activate that repository's runtime code in `shared-core`.

## Provenance and status

| Field | Recorded value |
| --- | --- |
| Source repository | `https://github.com/FishRaposo/operator-systems-template.git` |
| Source revision | `ac056271b0c7a9a92aa9430f5e1dc72fd8009f62` |
| Source role | Canonical starter template for Operator Systems services |
| Absorption date | 2026-08-12 |
| Target role | Reference material for `shared-core` maintainers and downstream service owners |
| Integration status | Documentation-only; no runtime, dependency, configuration, CI, or remote integration |

The source revision above is the only source snapshot represented by this guide. Later source changes require a new provenance review rather than an implied update here.

## What to reuse as a starter reference

Use these conventions when starting a service that consumes `shared-core`; choose only the parts that fit the service's ownership and deployment model.

1. Establish a service-owned configuration class derived from `shared_core.config.BaseAppConfig`, with secrets supplied through environment variables and an `.env.example` containing placeholders only.
2. Keep application concerns separate from the shared library: service routes, workers, models, migrations, and deployment configuration belong to the service repository, not to `shared-core`.
3. Adopt a documented local verification loop—tests, Ruff lint/format checks, and Pyright—without assuming the template's commands, paths, or CI are automatically installed in a consumer.
4. If a service needs PostgreSQL and Redis locally, define service-specific Compose names, ports, persistence, credentials, and network exposure. Do not copy the template's defaults blindly into a production environment.
5. Publish service-specific architecture, security, failure-mode, and roadmap documentation. The selected source documents below are examples of the questions those documents should answer, not inherited policy.

## Source-path mapping

| Source path at recorded revision | Reference retained here | Target location / use | Runtime status |
| --- | --- | --- | --- |
| `README.md` | Setup sequence, service naming checklist, expected documentation set | This guide: “What to reuse as a starter reference” | Reference only |
| `AGENTS.md` | Operator-facing command and ownership checklist | `AGENTS.md` migration-note section and this guide | Reference only |
| `docs/architecture.md` | Service boundary, component-map, and health-check documentation prompts | This guide: service-owned boundaries | Reference only |
| `docs/design-decisions.md` | Rationale template for tooling and infrastructure choices | This guide: verification and service-ownership guidance | Reference only |
| `docs/failure-modes.md` | Failure-mode documentation prompts for dependency and CI issues | This guide: service verification guidance | Reference only |
| `docs/security.md` | Environment-secret, validation, and network-boundary prompts | This guide: configuration and deployment guidance | Reference only |
| `docs/roadmap.md` | Scope and intentionally-not-building documentation pattern | This guide: scope boundary | Reference only |
| `docs/implementation_plan.md` | Service implementation and verification planning prompts | This guide: verification guidance | Reference only |
| `LICENSE` | License status | “License and attribution” below | No source file copied |

## Explicitly excluded runtime paths

The following source paths were reviewed as runtime or build material and are deliberately **not** copied or integrated by this absorption:

- `.github/`, `.pre-commit-config.yaml`, `Makefile`, `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `requirements.txt`, `pytest.ini`, `pyrightconfig.json`, `ruff.toml`, `.env.example`, and `.gitignore`
- `src/` (including `main.py`, `config.py`, `errors.py`, and `worker.py`)
- `tests/`, `examples/`, `alembic/`, and `alembic.ini`

These exclusions prevent this library from claiming that it has become a FastAPI service template, Celery worker, Docker deployment, CI workflow, database migration scaffold, or source-compatible fork of the source repository.

## License and attribution

The source repository contains an MIT License with copyright `Copyright (c) 2026 Operator Systems` at the recorded revision. This guide is an original summary and path map; it does not copy source code or substantial source documentation. Any future transfer of source text or files must preserve required MIT notices and be reviewed for scope, attribution, and compatibility before inclusion.

## Archive gate

**Archive status: not approved by this documentation task.** The source repository must remain available until its owner records that every intended consumer has either retained an independent starter path or explicitly adopted a replacement. Before any archive decision, verify the recorded source SHA, review downstream ownership, preserve the source URL and license notice, and obtain a separate approval. Passing `make check-migrations` validates this target guide only; it is not authorization to archive, delete, rename, or change remotes for the source repository.

## Maintenance rule

Run `make check-migrations` after editing this guide, its README/AGENTS references, or the provenance checker. If the source is revisited, add a dated migration record instead of silently changing the revision in this document.
