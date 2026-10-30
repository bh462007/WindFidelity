
from datetime import date

import requests
from fastapi.testclient import TestClient

from app.api import routes_metrics
from app.main import app
from app.services import analysis_service

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


def test_analyse_day_uses_elexon_client_and_retains_forecast_params(monkeypatch):
    captured = []
    forecast_validations = []
    actual_validations = []

    valid_actual = [{
        "businessType": "Wind generation",
        "startTime": "2026-10-26T00:00:00Z",
        "quantity": 100.0,
    }]
    invalid_actual = [{
        "businessType": "Wind generation",
        "startTime": "2026-10-26T00:30:00Z",
        "quantity": "bad",
    }]

    def fake_fetch_json(endpoint, params):
        captured.append((endpoint, params))

        if endpoint == "/generation/actual/per-type/wind-and-solar":
            return valid_actual + invalid_actual

        if endpoint == "/forecast/generation/wind/evolution":
            return [{
                "publishTime": "2026-10-25T10:00:00Z",
                "startTime": params["startTime"],
                "settlementDate": "2026-10-26",
                "settlementPeriod": 1,
                "generation": 90.0,
            }]

        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    def fake_validate_actual_generation_records(records):
        actual_validations.append(records)
        return {
            "valid_records": valid_actual,
            "invalid_records": [{"record": invalid_actual[0], "reason": "quantity must be numeric"}],
            "rejected_count": 1,
        }

    def fake_validate_windfor_records(records):
        forecast_validations.append(records)
        return {"valid_records": records, "invalid_records": [], "rejected_count": 0}

    monkeypatch.setattr(analysis_service.client, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(analysis_service, "validate_actual_generation_records", fake_validate_actual_generation_records)
    monkeypatch.setattr(analysis_service, "validate_windfor_records", fake_validate_windfor_records)
    monkeypatch.setattr(
        analysis_service,
        "aggregate_hourly_actuals",
        lambda rows: [{"startTime": row["startTime"], "actual_mw": 100.0} for row in rows],
    )
    monkeypatch.setattr(
        analysis_service,
        "match_forecasts_to_actuals",
        lambda forecasts, actuals: [{
            "startTime": forecasts[0]["startTime"],
            "publishTime": forecasts[0]["publishTime"],
            "forecast_mw": float(forecasts[0]["generation"]),
            "actual_mw": actuals[0]["actual_mw"],
        }],
    )
    monkeypatch.setattr(
        analysis_service,
        "calculate_metrics",
        lambda matched: {
            "sample_count": len(matched),
            "mae_mw": 0.0,
            "rmse_mw": 0.0,
            "bias_mw": 0.0,
        },
    )

    result = analysis_service.analyse_day(date(2026, 10, 26))

    assert actual_validations == [[*valid_actual, *invalid_actual]]
    assert len(forecast_validations) == 24
    assert all(len(group) == 1 for group in forecast_validations)
    assert all(
        group[0]["publishTime"] == "2026-10-25T10:00:00Z"
        and group[0]["settlementDate"] == "2026-10-26"
        and group[0]["settlementPeriod"] == 1
        and group[0]["generation"] == 90.0
        for group in forecast_validations
    )

    assert captured[0] == (
        "/generation/actual/per-type/wind-and-solar",
        {
            "from": "2026-10-26T00:00:00Z",
            "to": "2026-10-27T00:00:00Z",
            "format": "json",
        },
    )

    forecast_calls = [
        params for endpoint, params in captured if endpoint == "/forecast/generation/wind/evolution"
    ]
    assert len(forecast_calls) == 24
    assert all(call["format"] == "json" for call in forecast_calls)
    assert all("startTime" in call for call in forecast_calls)

    expected_hours = [
        f"2026-10-26T{hour:02d}:00:00Z"
        for hour in range(24)
    ]
    actual_hours = [call["startTime"] for call in forecast_calls]
    assert sorted(actual_hours) == expected_hours
    assert len(set(actual_hours)) == 24
    assert result["date"] == "2026-10-26"


def test_metrics_route_propagates_elexon_http_error(monkeypatch):
    def fake_fetch_json(endpoint, params):
        raise requests.HTTPError("502 Bad Gateway")

    monkeypatch.setattr(analysis_service.client, "fetch_json", fake_fetch_json)

    response = client.get(
        "/api/v1/metrics",
        params={"day": "2026-10-26"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not retrieve data from Elexon"}


def test_metrics_rejects_invalid_date():
    response = client.get(
        "/api/v1/metrics",
        params={"day": "not-a-date"},
    )

    assert response.status_code == 422
