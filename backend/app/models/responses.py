from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy"]


class ReadyResponse(BaseModel):
    status: Literal["ready", "warming"]
    cached_days: int


class ForecastCutoff(BaseModel):
    cutoff_utc: str
    policy: str


class Coverage(BaseModel):
    expected_hours: int
    matched_hours: int
    unmatched_hours: int


class Metrics(BaseModel):
    sample_count: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float


class MatchedPoint(BaseModel):
    startTime: str
    publishTime: str
    forecast_mw: float
    actual_mw: float


class SummaryResponse(BaseModel):
    date: str
    timezone: str
    forecast_cutoff: ForecastCutoff
    coverage: Coverage
    metrics: Metrics


class TimeseriesResponse(BaseModel):
    date: str
    timezone: str
    points: list[MatchedPoint]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody