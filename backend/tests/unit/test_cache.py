import pytest

from app.services.cache import TTLCache


def make_cache(ttl=60):
    now = [1000.0]
    return TTLCache(ttl_seconds=ttl, clock=lambda: now[0]), now


def test_returns_cached_value_within_ttl():
    cache, now = make_cache()
    calls = []

    def compute():
        calls.append(1)
        return {"call": len(calls)}

    assert cache.get_or_compute("k", compute) == {"call": 1}
    now[0] = 1059
    assert cache.get_or_compute("k", compute) == {"call": 1}
    assert len(calls) == 1


def test_recomputes_after_ttl_expires():
    cache, now = make_cache()
    calls = []

    def compute():
        calls.append(1)
        return {"call": len(calls)}

    cache.get_or_compute("k", compute)
    now[0] = 1060
    assert cache.get_or_compute("k", compute) == {"call": 2}


def test_does_not_cache_exceptions():
    cache, _ = make_cache()

    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        cache.get_or_compute("k", boom)

    assert cache.get_or_compute("k", lambda: "ok") == "ok"