
from collections import defaultdict
from datetime import datetime, timezone


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
