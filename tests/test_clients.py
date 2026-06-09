import httpx
import pytest
import respx

from shared_core.clients import BaseHTTPClient


@pytest.mark.asyncio
@respx.mock
async def test_base_http_client_get():
    client = BaseHTTPClient(base_url="https://api.example.com")

    # Mock endpoint
    route = respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"status": "success"})
    )

    response = await client.get("/data")
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    assert route.called

    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_base_http_client_retry():
    client = BaseHTTPClient(
        base_url="https://api.example.com", max_retries=2, backoff_factor=0.01
    )

    # Mock routes: 1st returns 500, 2nd returns 200
    route = respx.get("https://api.example.com/retry")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(200, json={"status": "ok"}),
    ]

    response = await client.get("/retry")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert route.call_count == 2

    await client.close()
