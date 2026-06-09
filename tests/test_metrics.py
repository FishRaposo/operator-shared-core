from shared_core.metrics import MetricsRegistry


def test_metrics_registry_creation():
    registry = MetricsRegistry("test-service")
    assert registry.service_name == "test-service"
    assert registry.http_requests_total is not None
    assert registry.http_request_duration_seconds is not None
    assert registry.db_connections_active is not None
    assert registry.errors_total is not None


def test_metrics_counter_increment():
    registry = MetricsRegistry("test-service")
    registry.http_requests_total.labels(
        service="test-service",
        method="GET",
        endpoint="/test",
        status="200",
    ).inc()
    registry.http_requests_total.labels(
        service="test-service",
        method="GET",
        endpoint="/test",
        status="200",
    ).inc()

    samples = registry.http_requests_total.collect()[0].samples
    total_samples = [s for s in samples if s.name.endswith("_total")]
    assert len(total_samples) == 1
    assert total_samples[0].value == 2


def test_metrics_histogram_observe():
    registry = MetricsRegistry("test-service")
    registry.http_request_duration_seconds.labels(
        service="test-service",
        method="POST",
        endpoint="/submit",
    ).observe(0.25)

    samples = registry.http_request_duration_seconds.collect()[0].samples
    sum_sample = [s for s in samples if s.name.endswith("_sum")][0]
    assert sum_sample.value == 0.25


def test_metrics_gauge_set():
    registry = MetricsRegistry("test-service")
    registry.db_connections_active.labels(
        service="test-service",
    ).set(10)

    samples = registry.db_connections_active.collect()[0].samples
    value_sample = [s for s in samples if s.name == "db_connections_active"][0]
    assert value_sample.value == 10
