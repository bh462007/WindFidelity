# WindFidelity

[![CI](https://github.com/bh462007/WindFidelity/actions/workflows/ci.yml/badge.svg)](https://github.com/bh462007/WindFidelity/actions/workflows/ci.yml)

![Dashboard](docs/dashboard.png)
*Dashboard for 15 January 2026.*

WindFidelity measures how accurate Elexon's day-ahead wind generation forecasts are for Great Britain. For any delivery day it compares what was forecast with what the grid actually produced, and reports the error in megawatts.

The central design rule is that a forecast is only scored using information that existed before the cutoff. That keeps the comparison honest.

## What it reports

For a chosen UTC day, hour by hour:

- **MAE**: average size of the miss.
- **RMSE**: like MAE, but large misses count more.
- **Bias**: average of forecast minus actual. Positive means the forecast ran above actual.
- **Coverage**: how many of the 24 hours had both a usable forecast and an actual.

The dashboard shows these as a summary strip, a forecast-vs-actual line chart, an hourly error chart, and a System Activity panel that lists real pipeline events (rows ingested, hours matched, cache hits and misses, failures).

## The cutoff rule

For each delivery hour, the forecast used is the **latest one published at or before 09:50 UTC on the previous calendar day**. A forecast published exactly at the cutoff is kept; one published a second later is rejected. If no forecast qualifies, that hour is unmatched and shows up in the coverage figure.

The cutoff time is configurable through the `FORECAST_CUTOFF_UTC` environment variable and defaults to `09:50`. The boundary cases (later rejected, earlier selected, exactly at cutoff selected, no candidate) are covered by unit tests.

## Data sources

Both come from the Elexon BMRS API. All timestamps are ISO 8601 in UTC.

| Data | Endpoint | Used for |
|---|---|---|
| FUELHH | `/datasets/FUELHH/stream` | Actual generation. Half-hourly `WIND` rows, averaged to hourly. |
| WINDFOR | `/forecast/generation/wind/evolution` | Forecast history. Each delivery hour has many publications (584 rows for 15 Jan 2026). |

## API

| Endpoint | Returns |
|---|---|
| `GET /api/v1/summary?day=YYYY-MM-DD` | Metrics, coverage and the cutoff policy |
| `GET /api/v1/timeseries?day=YYYY-MM-DD` | Per-hour forecast, actual and publish time |
| `GET /api/v1/activity?limit=50` | Recent pipeline events, newest first |
| `GET /health` | Liveness |
| `GET /ready` | `warming` until a day has been cached, then `ready` |

Every response has a typed Pydantic model. Errors use one envelope:

```json
{ "error": { "code": "no_data", "message": "..." } }
```

| Status | Code | Meaning |
|---|---|---|
| 503 | `upstream_unavailable` | Elexon could not be reached |
| 422 | `no_data` | No matching forecasts and actuals for that day |
| 422 | `invalid_request` | Malformed parameter |

Results are cached in memory for 5 minutes per day.

## Project layout

```
backend/
  app/
    api/          routes: metrics, activity, health
    ingestion/    Elexon client (retries, timeout) and record validation
    processing/   clean, match (the cutoff rule) and metrics
    services/     pipeline, TTL cache, activity ring buffer
    models/       Pydantic response models
  tests/          unit and integration tests
frontend/
  src/
    api/          typed client
    components/   summary, charts, states, System Activity
    hooks/        data loading
    lib/          downsampling and chart data
scripts/          fetch_sample.py captures raw Elexon responses as sample data
```

## Running it

You need Python 3.11 or newer and Node 20 or newer.

Backend, from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
uvicorn app.main:app --port 8000
```

Frontend, in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` and `/ready` to the backend on port 8000.

To change the cutoff, set the variable before starting the backend:

```powershell
$env:FORECAST_CUTOFF_UTC = "10:00"
```

## Tests and checks

```powershell
pytest -q                 # backend, from the repository root
ruff check backend

cd frontend
npm test
npm run build             # also type-checks
npm run lint
```

## Design decisions

- **Actuals come from FUELHH, not the per-type wind-and-solar endpoint.** The per-type endpoint reports onshore and offshore as separate rows at the same timestamp. A keep-last dedupe silently dropped onshore, understating actual generation by thousands of MW and inflating the apparent forecast error. This was caught by comparing the pipeline's output with the raw data.
- **Duplicate timestamps keep the last value and log a warning when values conflict.**
- **Only complete hours are scored.** An hour needs both its :00 and :30 readings.
- **Activity is recorded where things happen**, not simulated, and the panel is labelled System Activity because it polls rather than streams.
- **Chart rendering is capped at 500 points** using largest-triangle downsampling, which returns original points only and keeps peaks.

## What the data shows so far

Five January 2026 days were scored against two sources of "actual" wind. Bias is forecast minus actual, in MW.

| Day | Bias vs FUELHH wind | Bias vs per-type wind total |
|---|---|---|
| 5 Jan | +219 | −961 |
| 10 Jan | +856 | −432 |
| 15 Jan | +1,190 | −430 |
| 20 Jan | +318 | −2,684 |
| 25 Jan | +1,735 | −604 |

Against FUELHH the forecast ran above actual on every day. Against the per-type total (onshore plus offshore) it ran below actual on every day. The per-type total was roughly 1,200 to 3,000 MW higher than FUELHH on these days, so the choice of "actual" changes the sign of the bias as well as its size.

What this does show: the bias reported by the dashboard is relative to FUELHH wind and should not be read as proof that the forecast is biased. What it does not show: which measure WINDFOR is meant to forecast. Elexon defines WINDFOR as "a forecast of generation for all Power Park Modules" and does not say whether embedded wind is included.

## Known limitations

- The API analyses one day at a time. There is no multi-day range yet, so the downsampler is built and tested but not exercised by a normal day.
- The activity log and cache live in the backend process and reset when it restarts.
- There is no deployment configuration. The Vite proxy only exists in development, so a hosted version needs a reverse proxy or CORS settings.
- The default date in the dashboard is fixed rather than "latest available day".