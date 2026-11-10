from datetime import date
from typing import Annotated

import requests
from app.errors import ApiError
from app.models.responses import (
    ErrorResponse,
    PeriodResponse,
    SnapshotResponse,
    SummaryResponse,
    TimeseriesResponse,
)
from app.services import snapshot as snapshot_service
from app.services.activity import activity_log
from app.services.analysis_service import analyse_day, analyse_period
from app.services.cache import TTLCache
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1", tags=["metrics"])
cache = TTLCache(ttl_seconds=300)

ERROR_RESPONSES = {422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}

DayParam = Annotated[
    date, Query(description="UTC delivery date, formatted YYYY-MM-DD")
]
StartParam = Annotated[
    date, Query(description="First UTC delivery date, YYYY-MM-DD")
]
EndParam = Annotated[
    date, Query(description="Last UTC delivery date, YYYY-MM-DD, inclusive")
]


MAX_PERIOD_DAYS = 62


def _cached(key, label: str, analyse) -> dict:
    computed = False

    def compute() -> dict:
        nonlocal computed
        computed = True
        return analyse()

    try:
        result = cache.get_or_compute(key, compute)
    except requests.RequestException as exc:
        activity_log.record(
            "error",
            f"{label}: could not retrieve data from Elexon",
            day=label,
            code="upstream_unavailable",
        )
        raise ApiError(
            503, "upstream_unavailable", "Could not retrieve data from Elexon"
        ) from exc
    except ValueError as exc:
        activity_log.record(
            "error",
            f"{label}: {exc}",
            day=label,
            code="no_data",
        )
        raise ApiError(422, "no_data", str(exc)) from exc

    outcome = "miss" if computed else "hit"
    activity_log.record(
        "cache",
        f"{label}: cache {outcome}",
        day=label,
        result=outcome,
    )
    return result


def _analysis(day: date) -> dict:
    return _cached(day, day.isoformat(), lambda: analyse_day(day))


@router.get("/summary", response_model=SummaryResponse, responses=ERROR_RESPONSES)
def get_summary(day: DayParam):
    return _analysis(day)


@router.get(
    "/timeseries", response_model=TimeseriesResponse, responses=ERROR_RESPONSES
)
def get_timeseries(day: DayParam):
    result = _analysis(day)
    return {
        "date": result["date"],
        "timezone": result["timezone"],
        "points": result["matched_records"],
    }


@router.get("/period", response_model=PeriodResponse, responses=ERROR_RESPONSES)
def get_period(start: StartParam, end: EndParam):
    if end < start:
        raise ApiError(422, "invalid_request", "end must not be before start")
    if (end - start).days + 1 > MAX_PERIOD_DAYS:
        raise ApiError(
            422, "invalid_request", f"period must not exceed {MAX_PERIOD_DAYS} days"
        )

    label = f"{start.isoformat()}..{end.isoformat()}"
    result = _cached(("period", start, end), label, lambda: analyse_period(start, end))
    return {**result, "points": result["matched_records"]}


@router.get("/snapshot", response_model=SnapshotResponse, responses=ERROR_RESPONSES)
def get_snapshot():
    try:
        return snapshot_service.load_snapshot()
    except snapshot_service.SnapshotUnavailable as exc:
        raise ApiError(503, "snapshot_unavailable", "Snapshot is not available") from exc