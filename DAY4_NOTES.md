# Day 4 Report — Backend Finish

**Tests:** 69 passing
**Lint:** `ruff check backend` clean

## Outcome

| Done-when item | Status |
|---|---|
| Every endpoint returns the Pydantic shape | Done |
| 503 path tested | Done |
| `ruff check` clean | Done |
| `make test` green from a clean clone | Done: fresh clone, `pip install -r requirements.txt`, 69 tests pass, ruff clean (ran `pytest -q` directly; the Makefile itself was not run on Windows) |

## Endpoints

| Endpoint | Response model | Notes |
|---|---|---|
| `GET /health` | `HealthResponse` | `{"status": "healthy"}` |
| `GET /ready` | `ReadyResponse` | `warming` with 0 cached days, `ready` once at least one day is cached |
| `GET /api/v1/summary?day=` | `SummaryResponse` | date, timezone, forecast cutoff, coverage, metrics |
| `GET /api/v1/timeseries?day=` | `TimeseriesResponse` | per-hour matched points |

`/api/v1/metrics` was retired. Summary and timeseries read from the same cached analysis, so a day is fetched from Elexon once per 5 minutes.

## Error envelope

All errors use `{"error": {"code": ..., "message": ...}}`.

| Case | Status | Code |
|---|---|---|
| Elexon unreachable or HTTP error | 503 | `upstream_unavailable` |
| No eligible forecast/actual matches | 422 | `no_data` |
| Malformed query parameter | 422 | `invalid_request` |

The malformed-parameter case was found in the manual walkthrough: FastAPI's default `{"detail": [...]}` leaked through. Fixed with a handler, test first.

## Tests added

- `unit/test_responses.py`: model shape, missing field rejected, error envelope.
- `unit/test_cache.py`: `size()` counts only live entries.
- `integration/test_metrics_api.py`: summary without records, timeseries points, one shared computation, 503 envelope, 422 `no_data`, 422 `invalid_request`.
- `integration/test_health.py`: health shape, `/ready` warming, `/ready` reflects cached days.
- `conftest.py`: shared `client` fixture and an autouse cache-clearing fixture.

## Lint

`pyproject.toml` configures ruff: line length 100, rules `E`, `F`, `I`, `B`, fixtures excluded. The auto-fix mostly sorted imports; the remaining findings were an unused loop variable (three places), an unused `end` variable and some long test lines.

## Manual walkthrough (real Jan 2026 data)

Health, ready (warming then ready), summary, timeseries, the `no_data` envelope for a future date and the malformed-date case were all checked against the running server.

## Deviations from the plan

- `pytest.ini` stays at the repo root rather than `backend/`, so `pytest -q` from the root still works.
- `Makefile` targets Linux/CI. `make` was not used locally on Windows.
- `/ready` means "at least one day cached", not "Elexon is reachable".

## Open issues

- **Clean-clone check:** clone fresh, create a virtualenv, install `requirements.txt`, run `pytest -q`.
- **Misleading error code:** `ValueError("Unexpected response format from Elexon")` is also mapped to 422 `no_data`.
- **Unexplained positive bias** from Day 3 is still open.
- `backend/reports/sample_evaluation.json` is stale (it used the old offshore-only actuals).
- `ElexonClient.fetch_windfor` returns unvalidated rows; validation happens in `analysis_service`.