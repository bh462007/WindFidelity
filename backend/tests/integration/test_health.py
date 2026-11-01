from app.api import routes_metrics


def test_health_returns_typed_shape(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_is_warming_when_cache_is_empty(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "warming", "cached_days": 0}


def test_ready_reflects_cached_days(client):
    routes_metrics.cache.get_or_compute("some-day", lambda: {})

    response = client.get("/ready")

    assert response.json() == {"status": "ready", "cached_days": 1}