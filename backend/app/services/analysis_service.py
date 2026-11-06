
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

from app.config import FORECAST_CUTOFF_UTC
from app.ingestion.elexon_client import ElexonClient
from app.ingestion.schemas import (
    validate_windfor_records,
)
from app.processing.clean import aggregate_hourly_actuals
from app.processing.match import match_forecasts_to_actuals
from app.processing.metrics import calculate_metrics
from app.services.activity import activity_log

client = ElexonClient()


def analyse_day(day: date) -> dict:
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    
    actuals_df = client.fetch_fuelhh(day.isoformat())
    actuals_records = actuals_df.to_dict("records")

    activity_log.record(
        "ingestion",
        f"FUELHH {day.isoformat()}: {len(actuals_df)} wind rows loaded",
        source="FUELHH",
        day=day.isoformat(),
        rows=len(actuals_df),
    )

    delivery_times = [
        start + timedelta(hours=hour)
        for hour in range(24)
    ]

    def fetch_evolution(delivery):
        raw_group = client.fetch_json(
            "/forecast/generation/wind/evolution",
            {
                "startTime": delivery.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json",
            },
        )
        return validate_windfor_records(raw_group)

    with ThreadPoolExecutor(max_workers=6) as executor:
        validations = list(
            executor.map(fetch_evolution, delivery_times)
        )

    forecasts = [
        record
        for validation in validations
        for record in validation["valid_records"]
    ]
    rejected = sum(validation["rejected_count"] for validation in validations)
    activity_log.record(
        "ingestion",
        f"WINDFOR {day.isoformat()}: {len(forecasts)} forecast rows loaded, "
        f"{rejected} rejected",
        source="WINDFOR",
        day=day.isoformat(),
        rows=len(forecasts),
        rejected=rejected,
    )

    actuals = aggregate_hourly_actuals(actuals_records)
    matched = match_forecasts_to_actuals(forecasts, actuals)

    activity_log.record(
        "match",
        f"{day.isoformat()}: {len(matched)} of {len(delivery_times)} hours matched",
        day=day.isoformat(),
        matched_hours=len(matched),
        expected_hours=len(delivery_times),
    )

    if not matched:
        raise ValueError(
            f"No eligible forecast/actual matches for {day.isoformat()}"
        )

    cutoff_utc = FORECAST_CUTOFF_UTC.isoformat()

    return {
        "date": day.isoformat(),
        "timezone": "UTC",
        "coverage": {
            "expected_hours": len(delivery_times),
            "matched_hours": len(matched),
            "unmatched_hours": len(delivery_times) - len(matched),
        },
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
