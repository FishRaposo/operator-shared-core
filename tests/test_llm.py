import pytest

from shared_core.llm import LLMClientFactory, LLMResponse, estimate_llm_cost


def test_estimate_llm_cost():
    # gpt-4o-mini: 0.150 / 1M input, 0.600 / 1M output
    cost = estimate_llm_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert abs(cost - 0.75) < 1e-6

    # Test default fallback
    cost_fallback = estimate_llm_cost("unknown-model", 1000, 1000)
    assert cost_fallback > 0


@pytest.mark.asyncio
async def test_llm_client_factory_mock():
    factory = LLMClientFactory(openai_api_key="test-key")
    response = await factory.generate_mock("gpt-4o-mini", "Hello world")

    assert isinstance(response, LLMResponse)
    assert "Mock response" in response.text
    assert response.model == "gpt-4o-mini"
    assert response.prompt_tokens == 2
    assert response.completion_tokens > 0
    assert response.total_tokens == response.prompt_tokens + response.completion_tokens
    assert response.latency_ms > 0
    assert response.estimated_cost > 0
