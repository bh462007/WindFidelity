
from datetime import date, datetime, timedelta, timezone

from app.config import FORECAST_CUTOFF_UTC
from app.ingestion.elexon_client import ElexonClient
from app.ingestion.schemas import (
    validate_windfor_records,
)
from app.processing.clean import aggregate_hourly_actuals
from app.processing.match import get_forecast_cutoff, match_forecasts_to_actuals
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

    publish_from = start - timedelta(days=3)
    publish_to = get_forecast_cutoff(start)

    # One request for every forecast that could be in force for this delivery day.
    # A publication covers about 73 hours ahead, so nothing older than 3 days can
    # reach it. Nothing published after the cutoff is downloaded at all.
    raw_forecasts = client.fetch_windfor_stream(
        publish_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
        publish_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    validation = validate_windfor_records(raw_forecasts)
    forecasts = validation["valid_records"]
    rejected = validation["rejected_count"]
    
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
