import json

from shared_core.llm import estimate_llm_cost
from shared_core.pricing import (
    MODEL_PRICING,
    calculate_cost,
    load_pricing_override,
    register_pricing,
)


def test_calculate_cost_known_model():
    # gpt-4o-mini: 0.150 / 1M input, 0.600 / 1M output
    cost = calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert abs(cost - 0.75) < 1e-6


def test_calculate_cost_unknown_uses_default():
    cost = calculate_cost("totally-unknown-model", 1000, 1000)
    assert cost > 0


def test_prefix_match_for_dated_model_id():
    cost_exact = calculate_cost("claude-3-5-sonnet", 1000, 1000)
    cost_dated = calculate_cost("claude-3-5-sonnet-20241022", 1000, 1000)
    assert abs(cost_exact - cost_dated) < 1e-9


def test_estimate_llm_cost_delegates_to_pricing():
    # Backward-compat: the legacy llm.estimate_llm_cost matches pricing.calculate_cost.
    assert estimate_llm_cost("gpt-4o", 1000, 500) == calculate_cost("gpt-4o", 1000, 500)


def test_register_pricing_overrides():
    register_pricing("custom-model", 1.0, 2.0)
    assert MODEL_PRICING["custom-model"].input_per_1m == 1.0
    cost = calculate_cost("custom-model", 1_000_000, 1_000_000)
    assert abs(cost - 3.0) < 1e-6


def test_load_pricing_override_json(tmp_path):
    override = tmp_path / "prices.json"
    override.write_text(
        json.dumps({"my-model": {"input_per_1m": 9.0, "output_per_1m": 11.0}})
    )
    load_pricing_override(override)
    cost = calculate_cost("my-model", 1_000_000, 1_000_000)
    assert abs(cost - 20.0) < 1e-6
