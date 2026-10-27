
from app.processing.match import select_forecast_vintages



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

    result = select_forecast_vintages(forecasts)

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
