from datetime import date
from typing import Annotated

import requests
from app.errors import ApiError
from app.models.responses import ErrorResponse, SummaryResponse, TimeseriesResponse
from app.services.analysis_service import analyse_day
from app.services.cache import TTLCache
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1", tags=["metrics"])
cache = TTLCache(ttl_seconds=300)

ERROR_RESPONSES = {422: {"model": ErrorResponse}, 503: {"model": ErrorResponse}}

DayParam = Annotated[
    date, Query(description="UTC delivery date, formatted YYYY-MM-DD")
]


def _analysis(day: date) -> dict:
    try:
        return cache.get_or_compute(day, lambda: analyse_day(day))
    except requests.RequestException as exc:
        raise ApiError(
            503, "upstream_unavailable", "Could not retrieve data from Elexon"
        ) from exc
    except ValueError as exc:
        raise ApiError(422, "no_data", str(exc)) from exc


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