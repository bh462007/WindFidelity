import pytest
from app.models.responses import ErrorResponse, SummaryResponse
from pydantic import ValidationError

SUMMARY = {
    "date": "2026-01-15",
    "timezone": "UTC",
    "forecast_cutoff": {
        "cutoff_utc": "12:00:00",
        "policy": (
            "latest forecast published at or before 12:00:00 UTC "
            "on the previous calendar day"
        ),
    },
    "coverage": {"expected_hours": 24, "matched_hours": 24, "unmatched_hours": 0},
    "metrics": {"sample_count": 24, "mae_mw": 1189.79, "rmse_mw": 1289.02, "bias_mw": 1189.79},
}


def test_summary_accepts_pipeline_shape():
    assert SummaryResponse(**SUMMARY).metrics.sample_count == 24


def test_summary_rejects_missing_metrics():
    broken = {k: v for k, v in SUMMARY.items() if k != "metrics"}
    with pytest.raises(ValidationError):
        SummaryResponse(**broken)


def test_error_envelope_shape():
    body = ErrorResponse(error={"code": "upstream_unavailable", "message": "Elexon down"})
    assert body.model_dump() == {
        "error": {"code": "upstream_unavailable", "message": "Elexon down"}
    }