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


class Period(BaseModel):
    start: str
    end: str


class ErrorPercentiles(BaseModel):
    p50: float
    p90: float
    p95: float
    max: float


class DailyMetrics(Metrics):
    date: str


class HourlyMetrics(Metrics):
    hour: int


class PeriodResponse(BaseModel):
    period: Period
    timezone: str
    forecast_cutoff: ForecastCutoff
    coverage: Coverage
    metrics: Metrics
    error_percentiles: ErrorPercentiles
    daily: list[DailyMetrics]
    hourly: list[HourlyMetrics]
    points: list[MatchedPoint]


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


class ActivityEvent(BaseModel):
    id: int
    timestamp: str
    kind: Literal["ingestion", "match", "cache", "error"]
    message: str
    details: dict[str, str | int | float]


class ActivityResponse(BaseModel):
    events: list[ActivityEvent]
    capacity: int