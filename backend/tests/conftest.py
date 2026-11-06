import pytest
from app.api import routes_metrics
from app.main import app
from app.services.activity import activity_log
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_route_cache():
    routes_metrics.cache.clear()
    activity_log.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)