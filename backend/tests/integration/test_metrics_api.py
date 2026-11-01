import requests
from app.api import routes_metrics

POLICY = (
    "latest forecast published at or before 12:00:00 UTC "
    "on the previous calendar day"
)

ANALYSIS = {
    "date": "2026-01-15",
    "timezone": "UTC",
    "forecast_cutoff": {"cutoff_utc": "12:00:00", "policy": POLICY},
    "coverage": {"expected_hours": 24, "matched_hours": 1, "unmatched_hours": 23},
    "metrics": {"sample_count": 1, "mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0},
    "matched_records": [{
        "startTime": "2026-01-15T00:00:00Z",
        "publishTime": "2026-01-14T11:30:00Z",
        "forecast_mw": 110.0,
        "actual_mw": 100.0,
    }],
}


def test_summary_returns_typed_shape_without_records(client, monkeypatch):
    monkeypatch.setattr(routes_metrics, "analyse_day", lambda day: ANALYSIS)

    response = client.get("/api/v1/summary", params={"day": "2026-01-15"})

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["mae_mw"] == 10.0
    assert body["coverage"]["unmatched_hours"] == 23
    assert "matched_records" not in body


def test_timeseries_returns_points(client, monkeypatch):
    monkeypatch.setattr(routes_metrics, "analyse_day", lambda day: ANALYSIS)

    response = client.get("/api/v1/timeseries", params={"day": "2026-01-15"})

    assert response.status_code == 200
    assert response.json()["points"] == ANALYSIS["matched_records"]


def test_summary_and_timeseries_share_one_computation(client, monkeypatch):
    calls = []

    def fake(day):
        calls.append(day)
        return ANALYSIS

    monkeypatch.setattr(routes_metrics, "analyse_day", fake)

    client.get("/api/v1/summary", params={"day": "2026-01-15"})
    client.get("/api/v1/timeseries", params={"day": "2026-01-15"})

    assert len(calls) == 1


def test_upstream_failure_returns_503_envelope(client, monkeypatch):
    def boom(day):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(routes_metrics, "analyse_day", boom)

    response = client.get("/api/v1/summary", params={"day": "2026-01-15"})

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "upstream_unavailable",
            "message": "Could not retrieve data from Elexon",
        }
    }


def test_no_matches_returns_422_envelope(client, monkeypatch):
    def no_data(day):
        raise ValueError("No eligible forecast/actual matches for 2026-01-15")

    monkeypatch.setattr(routes_metrics, "analyse_day", no_data)

    response = client.get("/api/v1/timeseries", params={"day": "2026-01-15"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "no_data"


def test_invalid_date_returns_422_envelope(client):
    response = client.get("/api/v1/summary", params={"day": "not-a-date"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert "day" in error["message"]