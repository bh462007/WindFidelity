import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return None

    return parsed.astimezone(timezone.utc)


def _parse_date(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_fuelhh_record(record: dict) -> tuple[bool, str | None]:
    if not isinstance(record, dict):
        return False, "record is not an object"

    required = {
        "dataset": "FUELHH",
        "publishTime": str,
        "startTime": str,
        "settlementDate": str,
        "settlementPeriod": int,
        "fuelType": str,
        "generation": (int, float),
    }

    for field, expected in required.items():
        if field not in record or record[field] is None:
            return False, f"missing required field: {field}"

        value = record[field]

        if field == "dataset" and value != "FUELHH":
            return False, "dataset must be 'FUELHH'"

        if field in {"publishTime", "startTime"}:
            if _parse_utc_timestamp(value) is None:
                return False, f"invalid UTC timestamp for {field}"

        if field == "settlementDate" and _parse_date(value) is None:
            return False, "invalid settlementDate"

        if field == "settlementPeriod":
            if isinstance(value, bool) or not isinstance(value, int):
                return False, "settlementPeriod must be an integer"
            if value < 1 or value > 48:
                return False, "settlementPeriod out of range"

        if field == "fuelType":
            if not isinstance(value, str) or not value.strip():
                return False, "fuelType must be a non-empty string"

        if field == "generation":
            if not _is_number(value):
                return False, "generation must be numeric"

    return True, None


def _validate_windfor_record(record: dict) -> tuple[bool, str | None]:
    if not isinstance(record, dict):
        return False, "record is not an object"

    required = {
        "publishTime": str,
        "startTime": str,
        "settlementDate": str,
        "settlementPeriod": int,
        "generation": (int, float),
    }

    for field, expected in required.items():
        if field not in record or record[field] is None:
            return False, f"missing required field: {field}"

        value = record[field]

        if field in {"publishTime", "startTime"}:
            if _parse_utc_timestamp(value) is None:
                return False, f"invalid UTC timestamp for {field}"

        if field == "settlementDate" and _parse_date(value) is None:
            return False, "invalid settlementDate"

        if field == "settlementPeriod":
            if isinstance(value, bool) or not isinstance(value, int):
                return False, "settlementPeriod must be an integer"
            if value < 1 or value > 48:
                return False, "settlementPeriod out of range"

        if field == "generation":
            if not _is_number(value):
                return False, "generation must be numeric"

    return True, None


def validate_fuelhh_records(records: list[dict]) -> dict:
    valid_records = []
    invalid_records = []

    for record in records:
        is_valid, reason = _validate_fuelhh_record(record)
        if is_valid:
            valid_records.append(record)
        else:
            invalid_records.append({"record": record, "reason": reason})

    logger.info(
        "Validated %s FUELHH records: %s valid, %s rejected",
        len(records),
        len(valid_records),
        len(invalid_records),
    )

    return {
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "rejected_count": len(invalid_records),
    }


def validate_windfor_records(records: list[dict]) -> dict:
    valid_records = []
    invalid_records = []

    for record in records:
        is_valid, reason = _validate_windfor_record(record)
        if is_valid:
            valid_records.append(record)
        else:
            invalid_records.append({"record": record, "reason": reason})

    logger.info(
        "Validated %s WINDFOR records: %s valid, %s rejected",
        len(records),
        len(valid_records),
        len(invalid_records),
    )

    return {
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "rejected_count": len(invalid_records),
    }


def _validate_actual_generation_record(record: dict) -> tuple[bool, str | None]:
    if not isinstance(record, dict):
        return False, "record is not an object"

    required = {
        "businessType": str,
        "startTime": str,
        "quantity": (int, float),
    }

    for field, expected in required.items():
        if field not in record or record[field] is None:
            return False, f"missing required field: {field}"

        value = record[field]

        if field == "businessType":
            if not isinstance(value, str) or not value.strip():
                return False, "businessType must be a non-empty string"

        if field == "startTime":
            if _parse_utc_timestamp(value) is None:
                return False, "invalid UTC timestamp for startTime"

        if field == "quantity":
            if not _is_number(value):
                return False, "quantity must be numeric"

    return True, None


def validate_actual_generation_records(records: list[dict]) -> dict:
    valid_records = []
    invalid_records = []

    for record in records:
        is_valid, reason = _validate_actual_generation_record(record)
        if is_valid:
            valid_records.append(record)
        else:
            invalid_records.append({"record": record, "reason": reason})

    logger.info(
        "Validated %s actual-generation records: %s valid, %s rejected",
        len(records),
        len(valid_records),
        len(invalid_records),
    )

    return {
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "rejected_count": len(invalid_records),
    }


def normalize_fuelhh_records(records: list[dict]) -> list[dict]:
    normalized = []

    for record in records:
        if not isinstance(record, dict):
            continue

        if record.get("dataset") != "FUELHH":
            continue

        fuel_type = record.get("fuelType")
        if not isinstance(fuel_type, str) or fuel_type.upper() != "WIND":
            continue

        start_time = record.get("startTime")
        generation = record.get("generation")
        if start_time is None or generation is None:
            continue

        if _parse_utc_timestamp(start_time) is None or not _is_number(generation):
            continue

        normalized.append({
            "businessType": "Wind generation",
            "startTime": start_time,
            "quantity": float(generation),
        })

    return normalized
