import time

import pytest

from shared_core.tracing import (
    CostRecord,
    Span,
    SpanStatus,
    SpanType,
    Timer,
    new_trace_id,
    span,
)


def test_new_trace_id_unique():
    assert new_trace_id() != new_trace_id()


def test_span_records_duration_and_ok_status():
    with span("work", span_type=SpanType.TOOL, trace_id="t1") as current:
        time.sleep(0.001)
    assert current.trace_id == "t1"
    assert current.span_type == SpanType.TOOL
    assert current.status == SpanStatus.OK
    assert current.end_ms is not None
    assert current.duration_ms is not None and current.duration_ms >= 0


def test_span_marks_error_status_on_exception():
    captured = None
    with pytest.raises(ValueError):
        with span("boom", trace_id="t2") as current:
            captured = current
            raise ValueError("nope")
    assert captured is not None
    assert captured.status == SpanStatus.ERROR
    assert captured.end_ms is not None


def test_timer_elapsed_ms():
    with Timer() as timer:
        time.sleep(0.005)
    assert timer.elapsed_ms >= 4.0


def test_span_to_dict_is_json_serializable():
    s = Span(trace_id="t3", name="n", span_type=SpanType.LLM)
    payload = s.to_dict()
    assert payload["trace_id"] == "t3"
    assert payload["span_type"] == "llm"


def test_cost_record_defaults():
    record = CostRecord(model="gpt-4o", prompt_tokens=10, completion_tokens=5)
    assert record.total_tokens == 0
    assert record.estimated_cost == 0.0
