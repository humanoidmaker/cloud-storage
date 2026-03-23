import time

from app.middleware.rate_limiter import RateLimitStore


def test_allow_under_limit():
    store = RateLimitStore()
    limited, _ = store.is_rate_limited("test_key", 5, 60)
    assert limited is False


def test_block_at_limit():
    store = RateLimitStore()
    for _ in range(5):
        store.is_rate_limited("test_key", 5, 60)
    limited, retry_after = store.is_rate_limited("test_key", 5, 60)
    assert limited is True
    assert retry_after > 0


def test_rate_limit_resets():
    store = RateLimitStore()
    # Use a very short window
    for _ in range(5):
        store.is_rate_limited("test_key", 5, 1)
    time.sleep(1.1)
    limited, _ = store.is_rate_limited("test_key", 5, 1)
    assert limited is False


def test_different_ips_independent():
    store = RateLimitStore()
    for _ in range(5):
        store.is_rate_limited("ip1", 5, 60)
    limited_ip1, _ = store.is_rate_limited("ip1", 5, 60)
    limited_ip2, _ = store.is_rate_limited("ip2", 5, 60)
    assert limited_ip1 is True
    assert limited_ip2 is False


def test_retry_after_header():
    store = RateLimitStore()
    for _ in range(5):
        store.is_rate_limited("test_key", 5, 60)
    limited, retry_after = store.is_rate_limited("test_key", 5, 60)
    assert limited is True
    assert retry_after >= 1
