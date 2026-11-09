import math
from collections import defaultdict

from app.processing.metrics import calculate_metrics


def _group(matched: list[dict], key) -> dict:
    groups = defaultdict(list)
    for row in matched:
        groups[key(row)].append(row)
    return groups


def daily_metrics(matched: list[dict]) -> list[dict]:
    """Metrics per UTC delivery date, oldest first."""
    groups = _group(matched, lambda row: row["startTime"][:10])
    return [{"date": day, **calculate_metrics(groups[day])} for day in sorted(groups)]


def hourly_profile(matched: list[dict]) -> list[dict]:
    """Metrics per UTC hour of day, pooled across all days."""
    groups = _group(matched, lambda row: int(row["startTime"][11:13]))
    return [{"hour": hour, **calculate_metrics(groups[hour])} for hour in sorted(groups)]


def error_percentiles(matched: list[dict]) -> dict:
    """Nearest-rank percentiles of absolute error, in MW."""
    if not matched:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "max": 0.0}

    errors = sorted(abs(row["forecast_mw"] - row["actual_mw"]) for row in matched)

    def rank(p: float) -> float:
        return float(errors[math.ceil(p * len(errors)) - 1])

    return {"p50": rank(0.50), "p90": rank(0.90), "p95": rank(0.95), "max": float(errors[-1])}