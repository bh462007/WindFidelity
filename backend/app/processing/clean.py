
from collections import defaultdict
from datetime import datetime, timedelta, timezone


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def aggregate_hourly_actuals(records: list[dict]) -> list[dict]:
    by_timestamp = defaultdict(float)

    for row in records:
        if row.get("businessType") != "Wind generation":
            continue

        timestamp = row.get("startTime")
        quantity = row.get("quantity")

        if timestamp is None or quantity is None:
            continue

        try:
            timestamp_dt = parse_timestamp(timestamp)
            quantity = float(quantity)
        except (TypeError, ValueError):
            continue

        if not quantity >= 0:
            continue

        by_timestamp[timestamp_dt] += quantity

    by_hour = defaultdict(list)

    for timestamp, quantity in by_timestamp.items():
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        by_hour[hour].append((timestamp, quantity))

    results = []

    for hour in sorted(by_hour):
        readings = by_hour[hour]

        # Only accept a complete hour: one reading at :00 and one at :30.
        minutes = {timestamp.minute for timestamp, _ in readings}
        if len(readings) != 2 or minutes != {0, 30}:
            continue

        actual_mw = sum(quantity for _, quantity in readings) / 2

        results.append({
            "startTime": hour.isoformat().replace("+00:00", "Z"),
            "actual_mw": actual_mw,
        })

    return results


def _normalize_utc_bound(value, name: str):
    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = parse_timestamp(value)
    else:
        raise ValueError(f"{name} must be an ISO-8601 timestamp or datetime")

    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")

    return parsed.astimezone(timezone.utc)


def detect_missing_half_hourly_actuals(
    records: list[dict],
    start_utc: str | datetime | None = None,
    end_utc: str | datetime | None = None,
) -> dict:
    if (start_utc is None) != (end_utc is None):
        raise ValueError("start_utc and end_utc must be provided together")

    start_dt = _normalize_utc_bound(start_utc, "start_utc")
    end_dt = _normalize_utc_bound(end_utc, "end_utc")

    if start_dt is not None and end_dt is not None and start_dt >= end_dt:
        raise ValueError("start_utc must be before end_utc")

    by_timestamp = defaultdict(float)

    for row in records:
        if row.get("businessType") != "Wind generation":
            continue

        timestamp = row.get("startTime")
        quantity = row.get("quantity")

        if timestamp is None or quantity is None:
            continue

        try:
            timestamp_dt = parse_timestamp(timestamp)
            quantity = float(quantity)
        except (TypeError, ValueError):
            continue

        if quantity < 0:
            continue

        by_timestamp[timestamp_dt] += quantity

    if not by_timestamp and start_dt is None and end_dt is None:
        return {"missing_hours": [], "missing_half_hours": []}

    if start_dt is not None and end_dt is not None:
        window_start = start_dt.replace(minute=0, second=0, microsecond=0)
        window_end = end_dt
    else:
        window_start = min(by_timestamp).replace(minute=0, second=0, microsecond=0)
        window_end = max(by_timestamp).replace(
            minute=0, second=0, microsecond=0
        ) + timedelta(hours=1)

    missing_hours = []
    missing_half_hours = []

    current_hour = window_start
    while current_hour < window_end:
        expected = []
        for minute in (0, 30):
            candidate = current_hour.replace(minute=minute, second=0, microsecond=0)
            if start_dt is not None and end_dt is not None:
                if not (start_dt <= candidate < end_dt):
                    continue
            expected.append(candidate)

        if not expected:
            current_hour += timedelta(hours=1)
            continue

        present = [candidate for candidate in expected if candidate in by_timestamp]
        if not present:
            missing_hours.append(current_hour.isoformat().replace("+00:00", "Z"))
        else:
            for candidate in expected:
                if candidate not in by_timestamp:
                    missing_half_hours.append(
                        candidate.isoformat().replace("+00:00", "Z")
                    )

        current_hour += timedelta(hours=1)

    return {
        "missing_hours": missing_hours,
        "missing_half_hours": missing_half_hours,
    }
