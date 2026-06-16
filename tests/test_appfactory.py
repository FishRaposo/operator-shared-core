from fastapi import APIRouter
from fastapi.testclient import TestClient

from shared_core.appfactory import create_app


def test_create_app_health_static():
    app = create_app(service_name="svc-test")
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "service": "svc-test"}


def test_create_app_includes_routers_and_lifespan():
    router = APIRouter()
    events: list[str] = []

    @router.get("/ping")
    def ping() -> dict:
        return {"pong": True}

    async def on_startup() -> None:
        events.append("up")

    def on_shutdown() -> None:
        events.append("down")

    app = create_app(
        service_name="svc",
        routers=[router],
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        cors_origins=["http://localhost:3000"],
    )
    with TestClient(app) as client:
        assert client.get("/ping").json() == {"pong": True}
    assert events == ["up", "down"]
