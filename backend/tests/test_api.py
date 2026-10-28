
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_metrics

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_metrics_endpoint(monkeypatch):
    expected_result = {
        "date": "2026-10-26",
        "timezone": "UTC",
        "forecast_cutoff": {
            "cutoff_utc": "12:00:00",
            "policy": (
                "latest forecast published at or before 12:00:00 UTC "
                "on the previous calendar day"
            ),
        },
        "metrics": {
            "sample_count": 24,
            "mae_mw": 2646.27,
            "rmse_mw": 3030.11,
            "bias_mw": 2421.23,
        },
        "matched_records": [],
    }

    monkeypatch.setattr(
        routes_metrics,
        "analyse_day",
        lambda day: expected_result,
    )

    response = client.get(
        "/api/v1/metrics",
        params={"day": "2026-10-26"},
    )

    assert response.status_code == 200
    assert response.json() == expected_result


def test_metrics_rejects_invalid_date():
    response = client.get(
        "/api/v1/metrics",
        params={"day": "not-a-date"},
    )

    assert response.status_code == 422
