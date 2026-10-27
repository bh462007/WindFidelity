
from app.processing.clean import aggregate_hourly_actuals


def test_aggregates_onshore_and_offshore_and_averages_half_hours():
    records = [
        {
            "businessType": "Wind generation",
            "psrType": "Wind Onshore",
            "quantity": 60,
            "startTime": "2026-10-26T00:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "psrType": "Wind Offshore",
            "quantity": 40,
            "startTime": "2026-10-26T00:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "psrType": "Wind Onshore",
            "quantity": 50,
            "startTime": "2026-10-26T00:30:00Z",
        },
        {
            "businessType": "Wind generation",
            "psrType": "Wind Offshore",
            "quantity": 30,
            "startTime": "2026-10-26T00:30:00Z",
        },
    ]

    result = aggregate_hourly_actuals(records)

    assert len(result) == 1
    assert result[0]["actual_mw"] == 90


def test_drops_incomplete_hours():
    records = [{
        "businessType": "Wind generation",
        "quantity": 100,
        "startTime": "2026-10-26T00:00:00Z",
    }]

    assert aggregate_hourly_actuals(records) == []
