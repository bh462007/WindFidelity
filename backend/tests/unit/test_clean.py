
import pytest

from app.processing.clean import aggregate_hourly_actuals, detect_missing_half_hourly_actuals


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


def test_detects_missing_half_hour_in_an_hour():
    records = [{
        "businessType": "Wind generation",
        "quantity": 100,
        "startTime": "2026-10-26T00:00:00Z",
    }]

    result = detect_missing_half_hourly_actuals(records)

    assert result == {
        "missing_hours": [],
        "missing_half_hours": ["2026-10-26T00:30:00Z"],
    }


def test_detects_missing_hour_between_complete_hours():
    records = [
        {
            "businessType": "Wind generation",
            "quantity": 100,
            "startTime": "2026-10-26T00:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 80,
            "startTime": "2026-10-26T00:30:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 60,
            "startTime": "2026-10-26T02:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 70,
            "startTime": "2026-10-26T02:30:00Z",
        },
    ]

    result = detect_missing_half_hourly_actuals(records)

    assert result == {
        "missing_hours": ["2026-10-26T01:00:00Z"],
        "missing_half_hours": [],
    }


def test_detects_no_missing_data_for_complete_hours():
    records = [
        {
            "businessType": "Wind generation",
            "quantity": 90,
            "startTime": "2026-10-26T00:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 110,
            "startTime": "2026-10-26T00:30:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 70,
            "startTime": "2026-10-26T01:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 90,
            "startTime": "2026-10-26T01:30:00Z",
        },
    ]

    assert detect_missing_half_hourly_actuals(records) == {
        "missing_hours": [],
        "missing_half_hours": [],
    }


def test_detects_missing_first_half_hour_in_explicit_window():
    records = [{
        "businessType": "Wind generation",
        "quantity": 100,
        "startTime": "2026-10-26T00:30:00Z",
    }]

    result = detect_missing_half_hourly_actuals(
        records,
        start_utc="2026-10-26T00:00:00Z",
        end_utc="2026-10-26T01:00:00Z",
    )

    assert result == {
        "missing_hours": [],
        "missing_half_hours": ["2026-10-26T00:00:00Z"],
    }


def test_detects_missing_final_half_hour_in_explicit_window():
    records = [{
        "businessType": "Wind generation",
        "quantity": 100,
        "startTime": "2026-10-26T00:00:00Z",
    }]

    result = detect_missing_half_hourly_actuals(
        records,
        start_utc="2026-10-26T00:00:00Z",
        end_utc="2026-10-26T01:00:00Z",
    )

    assert result == {
        "missing_hours": [],
        "missing_half_hours": ["2026-10-26T00:30:00Z"],
    }


def test_detects_missing_hour_inside_explicit_window():
    records = [
        {
            "businessType": "Wind generation",
            "quantity": 80,
            "startTime": "2026-10-26T00:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 60,
            "startTime": "2026-10-26T00:30:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 50,
            "startTime": "2026-10-26T02:00:00Z",
        },
        {
            "businessType": "Wind generation",
            "quantity": 40,
            "startTime": "2026-10-26T02:30:00Z",
        },
    ]

    result = detect_missing_half_hourly_actuals(
        records,
        start_utc="2026-10-26T00:00:00Z",
        end_utc="2026-10-26T03:00:00Z",
    )

    assert result == {
        "missing_hours": ["2026-10-26T01:00:00Z"],
        "missing_half_hours": [],
    }


@pytest.mark.parametrize(
    "start_utc, end_utc",
    [
        ("2026-10-26T00:00:00", "2026-10-26T01:00:00Z"),
        ("2026-10-26T00:00:00Z", "2026-10-26T00:00:00"),
        ("2026-10-26T00:00:00Z", "2026-10-26T00:00:00Z"),
    ],
)
def test_rejects_invalid_bounds(start_utc, end_utc):
    with pytest.raises(ValueError):
        detect_missing_half_hourly_actuals([], start_utc=start_utc, end_utc=end_utc)
