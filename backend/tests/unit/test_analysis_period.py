from datetime import date

import pytest
from app.services import analysis_service


def _fuelhh(start, generation):
    return {
        "dataset": "FUELHH",
        "publishTime": "2026-02-01T00:00:00Z",
        "startTime": start,
        "settlementDate": start[:10],
        "settlementPeriod": 1,
        "fuelType": "WIND",
        "generation": generation,
    }


def _windfor(publish, start, generation):
    return {
        "dataset": "WINDFOR",
        "publishTime": publish,
        "startTime": start,
        "generation": generation,
    }


def test_analyse_period_uses_two_calls_and_the_cutoff_rule(monkeypatch):
    captured = []

    fuelhh_rows = [
        _fuelhh("2026-01-02T00:00:00Z", 100.0),
        _fuelhh("2026-01-02T00:30:00Z", 100.0),
        _fuelhh("2026-01-03T00:00:00Z", 200.0),
        _fuelhh("2026-01-03T00:30:00Z", 200.0),
    ]
    windfor_rows = [
        _windfor("2026-01-01T09:30:00Z", "2026-01-02T00:00:00Z", 110.0),
        _windfor("2026-01-01T10:30:00Z", "2026-01-02T00:00:00Z", 500.0),  # after cutoff
        _windfor("2026-01-02T09:30:00Z", "2026-01-03T00:00:00Z", 180.0),
    ]

    def fake_fetch_json(endpoint, params):
        captured.append((endpoint, params))
        if endpoint == "/datasets/FUELHH/stream":
            return fuelhh_rows
        if endpoint == "/datasets/WINDFOR/stream":
            return windfor_rows
        raise AssertionError(f"Unexpected endpoint: {endpoint}")

    monkeypatch.setattr(analysis_service.client, "fetch_json", fake_fetch_json)

    result = analysis_service.analyse_period(date(2026, 1, 2), date(2026, 1, 3))

    assert [c[0] for c in captured] == ["/datasets/FUELHH/stream", "/datasets/WINDFOR/stream"]
    assert captured[0][1]["settlementDateFrom"] == "2026-01-02"
    assert captured[0][1]["settlementDateTo"] == "2026-01-03"
    assert captured[1][1]["publishDateTimeFrom"] == "2025-12-30T00:00:00Z"
    assert captured[1][1]["publishDateTimeTo"] == "2026-01-02T09:50:00Z"

    assert result["period"] == {"start": "2026-01-02", "end": "2026-01-03"}
    assert result["coverage"] == {
        "expected_hours": 48,
        "matched_hours": 2,
        "unmatched_hours": 46,
    }
    # errors: +10 and -20 -> MAE 15, bias -5
    assert result["metrics"]["mae_mw"] == pytest.approx(15.0)
    assert result["metrics"]["bias_mw"] == pytest.approx(-5.0)
    assert [d["date"] for d in result["daily"]] == ["2026-01-02", "2026-01-03"]
    assert len(result["hourly"]) == 1
    assert result["error_percentiles"]["max"] == 20.0
    assert len(result["matched_records"]) == 2


def test_analyse_period_rejects_reversed_range():
    with pytest.raises(ValueError):
        analysis_service.analyse_period(date(2026, 1, 3), date(2026, 1, 2))