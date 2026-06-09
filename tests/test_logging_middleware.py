from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from loguru import logger

from shared_core.logging import (
    RequestLoggingMiddleware,
    correlation_id_var,
    setup_logging,
)


def test_logging_middleware():
    setup_logging(level="INFO", service_name="test-service")

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    def test_endpoint(request: Request):
        # Verify context variable is set during request
        assert correlation_id_var.get() is not None
        assert request.state.correlation_id == correlation_id_var.get()
        logger.info("Inside test endpoint logs")
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    # Assert correlation header is present in response
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] is not None


def test_logging_middleware_custom_header():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test-custom")
    def test_endpoint(request: Request):
        return {"id": correlation_id_var.get()}

    client = TestClient(app)
    # Pass correlation ID explicitly in request headers
    custom_id = "custom-uuid-1234"
    response = client.get("/test-custom", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.json()["id"] == custom_id
    assert response.headers["X-Correlation-ID"] == custom_id
