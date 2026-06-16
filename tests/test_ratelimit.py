from collections import deque

from shared_core.ratelimit import RateLimiter, sliding_window_allow


def test_sliding_window_allow_evicts_old_entries():
    timestamps: deque = deque()
    # First two within limit
    assert sliding_window_allow(timestamps, now=100.0, limit=2, window_seconds=60)
    assert sliding_window_allow(timestamps, now=101.0, limit=2, window_seconds=60)
    # Third exceeds the limit within the window
    assert not sliding_window_allow(timestamps, now=102.0, limit=2, window_seconds=60)
    # Far in the future: old entries evicted, allowed again
    assert sliding_window_allow(timestamps, now=200.0, limit=2, window_seconds=60)


def test_rate_limiter_in_memory_fallback():
    limiter = RateLimiter(redis_manager=None, limit=3, window_seconds=60)
    allowed = [limiter.allow("client-a") for _ in range(4)]
    assert allowed[:3] == [True, True, True]
    assert allowed[3] is False


def test_rate_limiter_keys_are_independent():
    limiter = RateLimiter(redis_manager=None, limit=1, window_seconds=60)
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False
