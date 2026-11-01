import pytest
from app.api import routes_metrics
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_route_cache():
    routes_metrics.cache.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)