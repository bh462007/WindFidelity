
from datetime import date

from app.main import app
from app.services import analysis_service
from app.services.activity import activity_log
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_analyse_day_makes_one_windfor_stream_call_for_the_decision_window(monkeypatch):
    captured = []
    forecast_validations = []

    fuelhh_rows = [{
        "dataset": "FUELHH",
        "publishTime": "2026-10-27T00:00:00Z",
        "startTime": "2026-10-26T00:00:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 1,
        "fuelType": "WIND",
        "generation": 100.0,
    }]

    windfor_rows = [{
        "dataset": "WINDFOR",
        "publishTime": "2026-10-25T09:30:00Z",
        "startTime": "2026-10-26T00:00:00Z",
        "generation": 90.0,
    }]

    def fake_fetch_json(endpoint, params):
        captured.append((endpoint, params))

        if endpoint == "/datasets/FUELHH/stream":
            return fuelhh_rows

        if endpoint == "/datasets/WINDFOR/stream":
            return windfor_rows

        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    def fake_validate_windfor_records(records):
        forecast_validations.append(records)
        return {
            "valid_records": records,
            "invalid_records": [],
            "rejected_count": 0,
        }

    monkeypatch.setattr(analysis_service.client, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(
        analysis_service, "validate_windfor_records", fake_validate_windfor_records
    )
    monkeypatch.setattr(
        analysis_service,
        "aggregate_hourly_actuals",
        lambda rows: [
            {"startTime": row["startTime"], "actual_mw": 100.0}
            for row in rows
        ],
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

    assert captured == [
        (
            "/datasets/FUELHH/stream",
            {
                "settlementDateFrom": "2026-10-26",
                "settlementDateTo": "2026-10-26",
                "format": "json",
            },
        ),
        (
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": "2026-10-23T00:00:00Z",
                "publishDateTimeTo": "2026-10-25T09:50:00Z",
                "format": "json",
            },
        ),
    ]
    assert forecast_validations == [windfor_rows]

    assert result["date"] == "2026-10-26"
    assert result["coverage"] == {
        "expected_hours": 24,
        "matched_hours": 1,
        "unmatched_hours": 23,
    }

    events = list(reversed(activity_log.recent()))
    assert [e["kind"] for e in events] == ["ingestion", "ingestion", "match"]
    assert events[0]["details"] == {"source": "FUELHH", "day": "2026-10-26", "rows": 1}
    assert events[1]["details"] == {
        "source": "WINDFOR",
        "day": "2026-10-26",
        "rows": 1,
        "rejected": 0,
    }
    assert events[2]["details"] == {
        "day": "2026-10-26",
        "matched_hours": 1,
        "expected_hours": 24,
    }


def test_metrics_rejects_invalid_date():
    response = client.get(
        "/api/v1/summary",
        params={"day": "not-a-date"},
    )

    assert response.status_code == 422

