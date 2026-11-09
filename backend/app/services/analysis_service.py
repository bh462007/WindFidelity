from datetime import date, datetime, timedelta, timezone

from app.config import FORECAST_CUTOFF_UTC
from app.ingestion.elexon_client import ElexonClient
from app.ingestion.schemas import validate_windfor_records
from app.processing.breakdown import daily_metrics, error_percentiles, hourly_profile
from app.processing.clean import aggregate_hourly_actuals
from app.processing.match import get_forecast_cutoff, match_forecasts_to_actuals
from app.processing.metrics import calculate_metrics
from app.services.activity import activity_log

client = ElexonClient()

_ISO_UTC = "%Y-%m-%dT%H:%M:%SZ"


def _midnight(day: date) -> datetime:
    return datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)


def _forecast_cutoff_info() -> dict:
    cutoff_utc = FORECAST_CUTOFF_UTC.isoformat()
    return {
        "cutoff_utc": cutoff_utc,
        "policy": (
            "latest forecast published at or before "
            f"{cutoff_utc} UTC on the previous calendar day"
        ),
    }


def _match_period(start: date, end: date) -> tuple[list[dict], int]:
    """Load actuals and forecasts for start..end (UTC delivery days) and match them.

    Two Elexon calls in total, however long the period is.
    """
    if end < start:
        raise ValueError("end must not be before start")

    label = start.isoformat() if start == end else f"{start.isoformat()}..{end.isoformat()}"
    expected_hours = 24 * ((end - start).days + 1)

    actuals_df = client.fetch_fuelhh(start.isoformat(), end.isoformat())
    actuals_records = actuals_df.to_dict("records")
    activity_log.record(
        "ingestion",
        f"FUELHH {label}: {len(actuals_df)} wind rows loaded",
        source="FUELHH",
        day=label,
        rows=len(actuals_df),
    )

    # A publication covers about 73 hours ahead, so anything older than 3 days
    # cannot reach the first delivery day. Nothing published after the cutoff
    # for the last delivery day is downloaded at all.
    publish_from = _midnight(start) - timedelta(days=3)
    publish_to = get_forecast_cutoff(_midnight(end))
    raw_forecasts = client.fetch_windfor_stream(
        publish_from.strftime(_ISO_UTC),
        publish_to.strftime(_ISO_UTC),
    )
    validation = validate_windfor_records(raw_forecasts)
    forecasts = validation["valid_records"]
    rejected = validation["rejected_count"]
    activity_log.record(
        "ingestion",
        f"WINDFOR {label}: {len(forecasts)} forecast rows loaded, {rejected} rejected",
        source="WINDFOR",
        day=label,
        rows=len(forecasts),
        rejected=rejected,
    )

    actuals = aggregate_hourly_actuals(actuals_records)
    matched = match_forecasts_to_actuals(forecasts, actuals)
    activity_log.record(
        "match",
        f"{label}: {len(matched)} of {expected_hours} hours matched",
        day=label,
        matched_hours=len(matched),
        expected_hours=expected_hours,
    )

    if not matched:
        raise ValueError(f"No eligible forecast/actual matches for {label}")

    return matched, expected_hours


def _coverage(matched: list[dict], expected_hours: int) -> dict:
    return {
        "expected_hours": expected_hours,
        "matched_hours": len(matched),
        "unmatched_hours": expected_hours - len(matched),
    }


def analyse_day(day: date) -> dict:
    matched, expected_hours = _match_period(day, day)

    return {
        "date": day.isoformat(),
        "timezone": "UTC",
        "coverage": _coverage(matched, expected_hours),
        "forecast_cutoff": _forecast_cutoff_info(),
        "metrics": calculate_metrics(matched),
        "matched_records": matched,
    }


def analyse_period(start: date, end: date) -> dict:
    matched, expected_hours = _match_period(start, end)

    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "timezone": "UTC",
        "coverage": _coverage(matched, expected_hours),
        "forecast_cutoff": _forecast_cutoff_info(),
        "metrics": calculate_metrics(matched),
        "error_percentiles": error_percentiles(matched),
        "daily": daily_metrics(matched),
        "hourly": hourly_profile(matched),
        "matched_records": matched,
    }