
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import requests

from app.processing.clean import aggregate_hourly_actuals
from app.processing.match import match_forecasts_to_actuals
from app.processing.metrics import calculate_metrics

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


def fetch_json(endpoint: str, params: dict) -> list[dict]:
    response = requests.get(
        f"{BASE_URL}{endpoint}",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict):
        data = data.get("data", [])

    if not isinstance(data, list):
        raise ValueError("Unexpected response format from Elexon")

    return data


def analyse_day(day: date) -> dict:
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    actuals_raw = fetch_json(
        "/generation/actual/per-type/wind-and-solar",
        {
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "format": "json",
        },
    )

    delivery_times = [
        start + timedelta(hours=hour)
        for hour in range(24)
    ]

    def fetch_evolution(delivery):
        return fetch_json(
            "/forecast/generation/wind/evolution",
            {
                "startTime": delivery.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json",
            },
        )

    with ThreadPoolExecutor(max_workers=6) as executor:
        history_groups = list(
            executor.map(fetch_evolution, delivery_times)
        )

    forecasts = [
        record
        for group in history_groups
        for record in group
    ]

    actuals = aggregate_hourly_actuals(actuals_raw)
    matched = match_forecasts_to_actuals(forecasts, actuals)

    if not matched:
        raise ValueError(
            f"No eligible forecast/actual matches for {day.isoformat()}"
        )

    return {
        "date": day.isoformat(),
        "timezone": "UTC",
        "minimum_lead_minutes": 120,
        "metrics": calculate_metrics(matched),
        "matched_records": matched,
    }
