import logging

from app.ingestion.schemas import (
    normalize_fuelhh_records,
    validate_actual_generation_records,
    validate_fuelhh_records,
    validate_windfor_records,
)


def test_validate_fuelhh_records_accepts_valid_record():
    record = {
        "dataset": "FUELHH",
        "publishTime": "2026-10-27T00:00:00Z",
        "startTime": "2026-10-26T23:30:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 48,
        "fuelType": "WIND",
        "generation": 1234,
    }

    result = validate_fuelhh_records([record])

    assert result["valid_records"] == [record]
    assert result["invalid_records"] == []
    assert result["rejected_count"] == 0


def test_validate_fuelhh_records_rejects_missing_required_fields():
    record = {
        "dataset": "FUELHH",
        "publishTime": "2026-10-27T00:00:00Z",
        "startTime": "2026-10-26T23:30:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 48,
        "fuelType": "WIND",
    }

    result = validate_fuelhh_records([record])

    assert result["valid_records"] == []
    assert result["rejected_count"] == 1
    assert result["invalid_records"][0]["reason"] == "missing required field: generation"


def test_validate_fuelhh_records_rejects_invalid_values():
    record = {
        "dataset": "FUELHH",
        "publishTime": "2026-10-27T00:00:00Z",
        "startTime": "2026-10-26T23:30:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 49,
        "fuelType": "WIND",
        "generation": "bad",
    }

    result = validate_fuelhh_records([record])

    assert result["rejected_count"] == 1
    assert result["invalid_records"][0]["reason"] in {
        "settlementPeriod out of range",
        "generation must be numeric",
    }


def test_validate_fuelhh_records_logs_rejected_count(caplog):
    record = {
        "dataset": "FUELHH",
        "publishTime": "2026-10-27T00:00:00Z",
        "startTime": "2026-10-26T23:30:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 48,
        "fuelType": "WIND",
        "generation": "bad",
    }

    with caplog.at_level(logging.INFO):
        result = validate_fuelhh_records([record])

    assert result["rejected_count"] == 1
    assert "1 rejected" in caplog.text


def test_validate_windfor_records_accepts_valid_record():
    record = {
        "publishTime": "2026-10-25T10:00:00Z",
        "startTime": "2026-10-26T00:00:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 1,
        "generation": 20500,
    }

    result = validate_windfor_records([record])

    assert result["valid_records"] == [record]
    assert result["invalid_records"] == []
    assert result["rejected_count"] == 0


def test_validate_windfor_records_rejects_missing_required_fields():
    record = {
        "publishTime": "2026-10-25T10:00:00Z",
        "startTime": "2026-10-26T00:00:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 1,
    }

    result = validate_windfor_records([record])

    assert result["valid_records"] == []
    assert result["rejected_count"] == 1
    assert result["invalid_records"][0]["reason"] == "missing required field: generation"


def test_validate_windfor_records_rejects_invalid_values():
    record = {
        "publishTime": "2026-10-25T10:00:00Z",
        "startTime": "2026-10-26T00:00:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 0,
        "generation": "bad",
    }

    result = validate_windfor_records([record])

    assert result["rejected_count"] == 1
    assert result["invalid_records"][0]["reason"] in {
        "settlementPeriod out of range",
        "generation must be numeric",
    }


def test_validate_windfor_records_logs_rejected_count(caplog):
    record = {
        "publishTime": "2026-10-25T10:00:00Z",
        "startTime": "2026-10-26T00:00:00Z",
        "settlementDate": "2026-10-26",
        "settlementPeriod": 1,
        "generation": "bad",
    }

    with caplog.at_level(logging.INFO):
        result = validate_windfor_records([record])

    assert result["rejected_count"] == 1
    assert "1 rejected" in caplog.text


def test_normalize_fuelhh_records_filters_non_wind_and_maps_to_cleaner_shape():
    records = [
        {
            "dataset": "FUELHH",
            "publishTime": "2026-10-27T00:00:00Z",
            "startTime": "2026-10-26T23:30:00Z",
            "settlementDate": "2026-10-26",
            "settlementPeriod": 48,
            "fuelType": "WIND",
            "generation": 1234,
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-10-27T00:00:00Z",
            "startTime": "2026-10-26T23:30:00Z",
            "settlementDate": "2026-10-26",
            "settlementPeriod": 48,
            "fuelType": "SOLAR",
            "generation": 999,
        },
        {
            "dataset": "FUELHH",
            "publishTime": "2026-10-27T00:00:00Z",
            "startTime": "2026-10-26T23:30:00Z",
            "settlementDate": "2026-10-26",
            "settlementPeriod": 48,
            "fuelType": "WIND",
            "generation": "bad",
        },
    ]

    assert normalize_fuelhh_records(records) == [{
        "businessType": "Wind generation",
        "startTime": "2026-10-26T23:30:00Z",
        "quantity": 1234.0,
    }]


def test_validate_fuelhh_records_rejects_malformed_batch_without_bypass():
    results = validate_fuelhh_records([{
        "startTime": "2026-10-26T23:30:00Z",
        "fuelType": "WIND",
        "generation": 1234,
    }])

    assert results["valid_records"] == []
    assert results["rejected_count"] == 1
    assert results["invalid_records"][0]["reason"] == "missing required field: dataset"


def test_validate_actual_generation_records_accepts_valid_raw_actual_rows():
    record = {
        "publishTime": "2026-10-27T02:30:01Z",
        "businessType": "Wind generation",
        "psrType": "Wind Onshore",
        "quantity": 7783.0,
        "startTime": "2026-10-27T00:00:00Z",
        "settlementDate": "2026-10-27",
        "settlementPeriod": 1,
    }

    result = validate_actual_generation_records([record])

    assert result["valid_records"] == [record]
    assert result["invalid_records"] == []
    assert result["rejected_count"] == 0


def test_validate_actual_generation_records_rejects_malformed_rows():
    result = validate_actual_generation_records([{
        "businessType": "Wind generation",
        "quantity": "bad",
        "startTime": "2026-10-27T00:00:00Z",
    }])

    assert result["valid_records"] == []
    assert result["rejected_count"] == 1
    assert result["invalid_records"][0]["reason"] == "quantity must be numeric"
