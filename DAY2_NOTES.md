# GridBricks — Day 2 Ingestion + Cleaning

## Goal

Fetch real January 2026 wind-generation data from the Elexon BMRS API, validate and normalize raw records, produce a clean canonical dataset, and verify the pipeline with tests.

## 1. API Ingestion

- **FUELHH actual generation:** Uses the Elexon FUELHH streaming endpoint:
  `/datasets/FUELHH/stream`
- **Date parameters:** `settlementDateFrom`, `settlementDateTo`, and `format=json`.
- **WINDFOR forecast history:** Uses `/forecast/generation/wind/evolution` with `startTime`.
- **HTTP behavior:** Requests use a 10-second timeout and retry handling for transient failures, including HTTP 429 and 5xx responses.
- **FUELHH range retrieval:** The streaming endpoint returned the complete January 2026 date range in one request. Conventional page/offset pagination was unnecessary.
- **Ordering:** Stream results arrive newest-first. The client sorts normalized records by `startTime` in ascending order.

## 2. Validation and Normalization

- Added validators for FUELHH, WINDFOR, and actual-generation records.
- Invalid records are rejected with a reason, and rejected-record counts are logged.
- FUELHH records are filtered to wind generation and normalized into:
  - `businessType`
  - `startTime`
  - `quantity`
- Actual-generation validation checks required fields, timezone-aware timestamps, and numeric quantities.

## 3. Cleaning Pipeline

The actual-generation cleaner performs the following operations:

1. Keeps records where `businessType` is `"Wind generation"`.
2. Parses timestamps and converts them to timezone-aware UTC datetimes.
3. Deduplicates records by timestamp.
4. Keeps the last record for a duplicate timestamp.
5. Logs a warning when duplicate records contain conflicting values.
6. Groups half-hourly readings into hourly values.
7. Produces an hourly value only when both expected half-hour readings (minute `00` and minute `30`) are present.
8. Averages the two half-hour readings to produce `generation_mw`.

The canonical cleaned output contains:

- `startTime` — timezone-aware UTC datetime.
- `generation_mw` — hourly wind generation in MW.

The missing-half-hour detection helper checks whether expected half-hour timestamps are present in the requested interval.

## 4. January 2026 Live-Data Verification

A live FUELHH request for January 1–31, 2026 completed successfully.

| Check | Result |
|---|---:|
| Raw FUELHH WIND records | 1,488 |
| Cleaned hourly records | 744 |
| First cleaned timestamp | `2026-01-01T00:00:00Z` |
| First cleaned generation value | `13,814.5 MW` |
| Missing hourly records | 0 |
| Missing half-hour records | 0 |

The FUELHH streaming endpoint was also tested directly for the full January range and returned **29,760 records** across fuel types in one response. The ingestion client validates and filters the response to wind records.

## 5. Tests

- Added unit tests for record validation and normalization.
- Added cleaning tests for wind filtering, duplicate handling, conflicting duplicate logging, and missing half-hour detection.
- Added ingestion-client tests for endpoint parameters, streaming behavior, normalization, empty responses, and HTTP failures.
- Added integration coverage for actual-generation validation in the analysis flow.

**Latest full test run:** `50 passed, 1 warning`.

The warning is a non-blocking Starlette deprecation warning related to using `httpx` with `starlette.testclient`. It did not cause test failures.

## 6. Git Status

The Day 2 cleaning/matching changes and the FUELHH streaming change were committed and pushed separately.

## 7. Important Implementation Decisions

- **Forecast cutoff remains unchanged:** D−1 at 12:00 UTC, as established on Day 1.
- **No invented pagination:** The verified FUELHH streaming endpoint returned the complete requested date range, so conventional page/offset pagination was not implemented.
- **Duplicate policy:** For a repeated timestamp, keep the last record; log a warning if duplicate values conflict.
- **Hourly aggregation:** Require both half-hour readings before emitting an hourly value; do not silently average incomplete hours.

