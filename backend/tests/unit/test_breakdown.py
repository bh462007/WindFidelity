import pytest
from app.processing.breakdown import daily_metrics, error_percentiles, hourly_profile


def _row(start, forecast, actual=100.0):
    return {
        "startTime": start,
        "publishTime": "2026-01-01T09:30:00Z",
        "forecast_mw": forecast,
        "actual_mw": actual,
    }


MATCHED = [
    _row("2026-01-02T00:00:00Z", 110.0),  # error +10
    _row("2026-01-02T01:00:00Z", 90.0),   # error -10
    _row("2026-01-03T00:00:00Z", 130.0),  # error +30
]


def test_daily_metrics_groups_by_utc_date():
    result = daily_metrics(MATCHED)

    assert [r["date"] for r in result] == ["2026-01-02", "2026-01-03"]
    assert result[0]["sample_count"] == 2
    assert result[0]["mae_mw"] == pytest.approx(10.0)
    assert result[0]["bias_mw"] == pytest.approx(0.0)
    assert result[1]["mae_mw"] == pytest.approx(30.0)
    assert result[1]["bias_mw"] == pytest.approx(30.0)


def test_hourly_profile_groups_by_hour_of_day_across_days():
    result = hourly_profile(MATCHED)

    assert [r["hour"] for r in result] == [0, 1]
    assert result[0]["sample_count"] == 2           # 02 Jan 00:00 and 03 Jan 00:00
    assert result[0]["mae_mw"] == pytest.approx(20.0)
    assert result[0]["bias_mw"] == pytest.approx(20.0)
    assert result[0]["rmse_mw"] == pytest.approx(500 ** 0.5)
    assert result[1]["bias_mw"] == pytest.approx(-10.0)


def test_error_percentiles_use_absolute_error_nearest_rank():
    # absolute errors 1..10, with alternating signs
    rows = [
        _row(f"2026-01-02T{i:02d}:00:00Z", 100.0 + i * (-1) ** i)
        for i in range(1, 11)
    ]

    result = error_percentiles(rows)

    assert result == {"p50": 5.0, "p90": 9.0, "p95": 10.0, "max": 10.0}


def test_empty_input_gives_empty_breakdowns():
    assert daily_metrics([]) == []
    assert hourly_profile([]) == []
    assert error_percentiles([]) == {"p50": 0.0, "p90": 0.0, "p95": 0.0, "max": 0.0}