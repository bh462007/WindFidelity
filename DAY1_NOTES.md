# GridBricks — Day 1 Data Verification

- **Endpoints:** FUELHH: `/datasets/FUELHH` using `settlementDateFrom` and `settlementDateTo`; WINDFOR: `/forecast/generation/wind/evolution` using `startTime`.
- **Actual generation:** Use FUELHH records with `fuelType = "WIND"`. The October 26, 2026 sample contains 48 half-hourly records. All 48 timestamps align with the existing actual wind endpoint; its additional timestamp is the next-day boundary and must be excluded.
- **Forecast history:** 578 WINDFOR records were retrieved for October 26, 2026. The 24 hourly delivery times have multiple distinct `publishTime` values. Forecast selection uses the latest publication at or before 12:00 UTC on the previous calendar day.
- **Timestamp format:** ISO 8601 UTC, using `Z` or an explicit UTC offset.
- **Cutoff status:** Fixed day-ahead cutoff selected: D-1 at 12:00 UTC. Configured through `FORECAST_CUTOFF_UTC`, defaulting to `12:00`. Forecasts published after the cutoff are excluded.
- **Fixtures:** `fuelhh_sample.json` and `windfor_sample.json` saved under `backend/tests/fixtures/`. The raw forecast history is also saved as `windfor_history_sample.json` for inspection.