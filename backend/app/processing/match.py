
from datetime import datetime, timedelta, timezone

from app.config import FORECAST_MIN_LEAD_MINUTES


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")

    return parsed.astimezone(timezone.utc)


def select_forecast_vintages(
    forecasts: list[dict],
    min_lead_minutes: int = FORECAST_MIN_LEAD_MINUTES,
) -> list[dict]:
    """Select the latest eligible forecast for each delivery time."""

    if min_lead_minutes < 0:
        raise ValueError("Minimum lead time cannot be negative")

    latest_by_delivery = {}

    for forecast in forecasts:
        published_value = forecast.get("publishTime")
        delivery_value = forecast.get("startTime")

        if not published_value or not delivery_value:
            continue

        published = parse_timestamp(published_value)
        delivery = parse_timestamp(delivery_value)

        if published > delivery - timedelta(minutes=min_lead_minutes):
            continue

        key = delivery.isoformat()
        current = latest_by_delivery.get(key)

        if current is None or published > parse_timestamp(
            current["publishTime"]
        ):
            latest_by_delivery[key] = forecast

    return [
        latest_by_delivery[key]
        for key in sorted(latest_by_delivery)
    ]



def match_forecasts_to_actuals(
    forecasts: list[dict],
    actuals: list[dict],
) -> list[dict]:
    selected = select_forecast_vintages(forecasts)

    actual_by_time = {
        parse_timestamp(row["startTime"]): float(row["actual_mw"])
        for row in actuals
    }

    matched = []

    for forecast in selected:
        delivery = parse_timestamp(forecast["startTime"])

        if delivery not in actual_by_time:
            continue

        matched.append({
            "startTime": forecast["startTime"],
            "publishTime": forecast["publishTime"],
            "forecast_mw": float(forecast["generation"]),
            "actual_mw": actual_by_time[delivery],
        })

    return matched
