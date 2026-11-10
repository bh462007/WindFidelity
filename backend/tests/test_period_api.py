import requests
from app.api import routes_metrics

FAKE_PERIOD = {
    "period": {"start": "2026-01-02", "end": "2026-01-03"},
    "timezone": "UTC",
    "forecast_cutoff": {"cutoff_utc": "09:50:00", "policy": "test policy"},
    "coverage": {"expected_hours": 48, "matched_hours": 1, "unmatched_hours": 47},
    "metrics": {"sample_count": 1, "mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0},
    "error_percentiles": {"p50": 10.0, "p90": 10.0, "p95": 10.0, "max": 10.0},
    "daily": [
        {
            "date": "2026-01-02",
            "sample_count": 1,
            "mae_mw": 10.0,
            "rmse_mw": 10.0,
            "bias_mw": 10.0,
        }
    ],
    "hourly": [
        {"hour": 0, "sample_count": 1, "mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0}
    ],
    "matched_records": [
        {
            "startTime": "2026-01-02T00:00:00Z",
            "publishTime": "2026-01-01T09:30:00Z",
            "forecast_mw": 110.0,
            "actual_mw": 100.0,
        }
    ],
}

URL = "/api/v1/period?start=2026-01-02&end=2026-01-03"


def test_period_returns_breakdowns_and_points(client, monkeypatch):
    monkeypatch.setattr(routes_metrics, "analyse_period", lambda start, end: FAKE_PERIOD)

    response = client.get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["period"] == {"start": "2026-01-02", "end": "2026-01-03"}
    assert body["error_percentiles"]["p90"] == 10.0
    assert body["daily"][0]["date"] == "2026-01-02"
    assert body["hourly"][0]["hour"] == 0
    assert body["points"] == FAKE_PERIOD["matched_records"]
    assert "matched_records" not in body


def test_period_is_computed_once_per_range(client, monkeypatch):
    calls = []

    def fake(start, end):
        calls.append((start, end))
        return FAKE_PERIOD

    monkeypatch.setattr(routes_metrics, "analyse_period", fake)

    client.get(URL)
    client.get(URL)

    assert len(calls) == 1


def test_reversed_range_is_an_invalid_request(client):
    response = client.get("/api/v1/period?start=2026-01-03&end=2026-01-02")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_overlong_range_is_an_invalid_request(client):
    response = client.get("/api/v1/period?start=2026-01-01&end=2026-12-31")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_missing_parameter_uses_the_error_envelope(client):
    response = client.get("/api/v1/period?start=2026-01-02")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_upstream_failure_is_a_503_envelope(client, monkeypatch):
    def fail(start, end):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(routes_metrics, "analyse_period", fail)

    response = client.get(URL)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "upstream_unavailable"