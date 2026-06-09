"""Metrics and observability utilities using prometheus_client.

prometheus_client is an optional dependency — dynamically imported
at runtime, following the same pattern as openai/anthropic in llm.py
and celery in tasks.py.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def _get_metrics():
    try:
        from prometheus_client import (  # type: ignore
            REGISTRY,
            Counter,
            Gauge,
            Histogram,
            generate_latest,
        )

        return Counter, Histogram, Gauge, generate_latest, REGISTRY
    except ImportError:
        raise ImportError(
            "prometheus_client is not installed. "
            "Install it via 'pip install prometheus-client' in your service."
        ) from None


class MetricsRegistry:
    """Holds pre-defined Prometheus metrics for HTTP services.

    Each instance uses its own CollectorRegistry to avoid metric name
    collisions when multiple registries exist (e.g., in tests).
    """

    def __init__(self, service_name: str):
        from prometheus_client import CollectorRegistry  # type: ignore

        Counter, Histogram, Gauge, _, _ = _get_metrics()
        self._registry = CollectorRegistry(auto_describe=True)

        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["service", "method", "endpoint", "status"],
            registry=self._registry,
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["service", "method", "endpoint"],
            registry=self._registry,
        )
        self.db_connections_active = Gauge(
            "db_connections_active",
            "Active database connections",
            ["service"],
            registry=self._registry,
        )
        self.errors_total = Counter(
            "errors_total",
            "Total application errors",
            ["service", "error_type"],
            registry=self._registry,
        )
        self.service_name = service_name


class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that instruments all HTTP requests."""

    def __init__(self, app, registry: MetricsRegistry):
        super().__init__(app)
        self.registry = registry

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        endpoint = request.url.path

        self.registry.http_requests_total.labels(
            service=self.registry.service_name,
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code),
        ).inc()

        self.registry.http_request_duration_seconds.labels(
            service=self.registry.service_name,
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        return response


def metrics_endpoint(registry: MetricsRegistry):
    """Returns a FastAPI endpoint that exposes Prometheus metrics."""
    _, _, _, generate_latest, _ = _get_metrics()

    async def metrics():
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(
            content=generate_latest(registry._registry),
            media_type="text/plain; version=0.0.4",
        )

    return metrics
