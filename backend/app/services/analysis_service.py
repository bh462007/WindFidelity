
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

from app.config import FORECAST_CUTOFF_UTC
from app.ingestion.elexon_client import ElexonClient
from app.processing.clean import aggregate_hourly_actuals
from app.processing.match import match_forecasts_to_actuals
from app.processing.metrics import calculate_metrics


client = ElexonClient()


def analyse_day(day: date) -> dict:
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    actuals_raw = client.fetch_json(
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
        return client.fetch_json(
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

    cutoff_utc = FORECAST_CUTOFF_UTC.isoformat()

    return {
        "date": day.isoformat(),
        "timezone": "UTC",
        "forecast_cutoff": {
            "cutoff_utc": cutoff_utc,
            "policy": (
                "latest forecast published at or before "
                f"{cutoff_utc} UTC on the previous calendar day"
            ),
        },
        "metrics": calculate_metrics(matched),
        "matched_records": matched,
    }
