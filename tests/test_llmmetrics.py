from shared_core.llmmetrics import LLMMetrics


def test_record_defaults_cost_from_pricing():
    m = LLMMetrics()
    call = m.record(
        model="gpt-4o-mini",
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
        latency_ms=120.0,
    )
    # gpt-4o-mini: 0.15 + 0.60 per 1M = 0.75
    assert abs(call.cost_usd - 0.75) < 1e-6


def test_summary_aggregates():
    m = LLMMetrics()
    m.record(
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
        latency_ms=100.0,
        prompt_version="v1",
    )
    m.record(
        model="gpt-4o",
        prompt_tokens=200,
        completion_tokens=80,
        latency_ms=300.0,
        prompt_version="v2",
        error="timeout",
    )
    s = m.summary()
    assert s["total_requests"] == 2
    assert s["input_tokens"] == 300
    assert s["output_tokens"] == 130
    assert s["total_tokens"] == 430
    assert s["error_rate"] == 0.5
    assert s["average_latency_ms"] == 200.0
    assert s["p50_latency_ms"] >= 100.0
    assert set(s["cost_by_prompt_version"]) == {"v1", "v2"}
    assert "gpt-4o" in s["cost_by_model"]


def test_empty_summary():
    s = LLMMetrics().summary()
    assert s["total_requests"] == 0
    assert s["error_rate"] == 0.0
    assert s["p95_latency_ms"] == 0.0
