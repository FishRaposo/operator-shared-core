"""FastAPI application factory encapsulating the standard service wiring.

Optional helper that builds a FastAPI app with shared_core logging, the typed error
handler, request-logging + CORS middleware, and ``/health``, so services don't repeat
the boilerplate. Existing services may keep their hand-written ``main.py``; new code can
use this to stay DRY.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Optional, Sequence, Union

_MaybeAsync = Union[Callable[[], None], Callable[[], Awaitable[None]]]


async def _maybe_await(fn: Optional[_MaybeAsync]) -> None:
    if fn is None:
        return
    result = fn()
    if hasattr(result, "__await__"):
        await result  # type: ignore[misc]


def create_app(
    *,
    service_name: str,
    title: Optional[str] = None,
    version: str = "0.1.0",
    description: str = "",
    log_level: str = "INFO",
    db_manager: Any = None,
    redis_manager: Any = None,
    cors_origins: Optional[Sequence[str]] = None,
    routers: Optional[Sequence[Any]] = None,
    on_startup: Optional[_MaybeAsync] = None,
    on_shutdown: Optional[_MaybeAsync] = None,
    enable_request_logging: bool = True,
) -> Any:
    """Build a configured FastAPI app.

    Args:
        service_name: logical service name (used for logging + ``/health``).
        db_manager / redis_manager: when ``db_manager`` is set, ``/health`` probes both
            via ``shared_core.health.check_health``; else it returns a static payload.
        cors_origins: list of allowed origins (CORS middleware added when non-empty).
        routers: FastAPI ``APIRouter`` instances to include.
        on_startup / on_shutdown: optional sync or async lifespan callbacks.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from shared_core.errors import BaseApplicationError, application_error_handler
    from shared_core.logging import RequestLoggingMiddleware, setup_logging

    setup_logging(level=log_level, service_name=service_name)

    @asynccontextmanager
    async def lifespan(app: "FastAPI"):  # noqa: F821
        await _maybe_await(on_startup)
        yield
        await _maybe_await(on_shutdown)

    app = FastAPI(
        title=title or service_name,
        version=version,
        description=description,
        lifespan=lifespan,
    )
    app.add_exception_handler(BaseApplicationError, application_error_handler)
    if enable_request_logging:
        app.add_middleware(RequestLoggingMiddleware)
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict:
        if db_manager is not None:
            from shared_core.health import check_health

            return check_health(db_manager, redis_manager, service_name)
        return {"status": "healthy", "service": service_name}

    for router in routers or []:
        app.include_router(router)

    return app
