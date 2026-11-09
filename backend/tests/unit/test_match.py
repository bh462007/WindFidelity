
from datetime import datetime, time, timezone

from app.processing.match import match_forecasts_to_actuals, select_forecast_vintages


def test_selects_latest_eligible_forecast():
    forecasts = [
        {
            "startTime": "2026-10-26T12:00:00Z",
            "publishTime": "2026-10-25T09:00:00Z",
            "generation": 100,
        },
        {
            "startTime": "2026-10-26T12:00:00Z",
            "publishTime": "2026-10-25T10:00:00Z",
            "generation": 110,
        },
        {
            "startTime": "2026-10-26T12:00:00Z",
            "publishTime": "2026-10-25T11:00:00Z",
            "generation": 120,
        },
        {
            "startTime": "2026-10-26T12:00:00Z",
            "publishTime": "2026-10-25T13:00:00Z",
            "generation": 130,
        },
    ]

    result = select_forecast_vintages(forecasts, cutoff=time(12, 0))

    assert len(result) == 1
    assert result[0]["publishTime"] == "2026-10-25T11:00:00Z"
    assert result[0]["generation"] == 120



def test_excludes_forecasts_published_after_delivery():
    forecasts = [
        {
            "startTime": "2026-10-26T12:00:00Z",
            "publishTime": "2026-10-26T12:30:00Z",
            "generation": 100,
        }
    ]

    assert select_forecast_vintages(forecasts) == []


def test_skips_records_with_missing_timestamps():
    forecasts = [{"generation": 100}]

    assert select_forecast_vintages(forecasts) == []


def _forecast(publish_time, generation):
    return {
        "startTime": "2026-10-26T12:00:00Z",
        "publishTime": publish_time,
        "generation": generation,
    }


def test_forecast_published_exactly_at_cutoff_is_selected():
    forecasts = [
        _forecast("2026-10-25T11:00:00Z", 100),
        _forecast("2026-10-25T12:00:00Z", 200),
        _forecast("2026-10-25T12:00:01Z", 300),
    ]

    result = select_forecast_vintages(forecasts, cutoff=time(12, 0))

    assert len(result) == 1
    assert result[0]["generation"] == 200


def test_no_candidate_at_or_before_cutoff_returns_nothing():
    forecasts = [_forecast("2026-10-25T12:00:01Z", 300)]

    assert select_forecast_vintages(forecasts) == []


def test_matches_forecast_to_actual_with_datetime_start_time():
    forecasts = [{
        "startTime": "2026-10-26T12:00:00Z",
        "publishTime": "2026-10-25T11:00:00Z",
        "generation": 120,
    }]
    actuals = [{
        "startTime": datetime(2026, 10, 26, 12, tzinfo=timezone.utc),
        "generation_mw": 100.0,
    }]

    assert match_forecasts_to_actuals(forecasts, actuals, cutoff=time(12, 0)) == [{
        "startTime": "2026-10-26T12:00:00Z",
        "publishTime": "2026-10-25T11:00:00Z",
        "forecast_mw": 120.0,
        "actual_mw": 100.0,
    }]


def test_cutoff_is_a_parameter_not_a_hidden_global():
    forecasts = [
        _forecast("2026-10-25T09:30:00Z", 100),
        _forecast("2026-10-25T11:30:00Z", 200),
    ]

    early = select_forecast_vintages(forecasts, cutoff=time(9, 50))
    late = select_forecast_vintages(forecasts, cutoff=time(12, 0))

    assert early[0]["generation"] == 100
    assert late[0]["generation"] == 200


def test_matching_uses_the_cutoff_it_is_given():
    forecasts = [
        _forecast("2026-10-25T09:30:00Z", 100),
        _forecast("2026-10-25T11:30:00Z", 200),
    ]
    actuals = [{
        "startTime": datetime(2026, 10, 26, 12, tzinfo=timezone.utc),
        "generation_mw": 90.0,
    }]

    matched = match_forecasts_to_actuals(forecasts, actuals, cutoff=time(9, 50))

    assert matched[0]["forecast_mw"] == 100.0


def test_default_cutoff_is_day_ahead_gate_closure():
    from app.config import FORECAST_CUTOFF_UTC

    assert FORECAST_CUTOFF_UTC == time(9, 50)


def test_default_cutoff_boundary_is_inclusive():
    forecasts = [
        _forecast("2026-10-25T09:50:00Z", 100),
        _forecast("2026-10-25T09:50:01Z", 200),
    ]

    result = select_forecast_vintages(forecasts)

    assert len(result) == 1
    assert result[0]["generation"] == 100