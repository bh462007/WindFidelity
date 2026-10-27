# GridBricks — Day 1 Data Verification

- **Endpoints:** FUELHH: `/datasets/FUELHH` using `settlementDateFrom` and `settlementDateTo`; WINDFOR: `/forecast/generation/wind/evolution` using `startTime`.
- **Actual generation:** Use FUELHH records with `fuelType = "WIND"`. The October 26, 2026 sample contains 48 half-hourly records. All 48 timestamps align with the existing actual wind endpoint; its additional timestamp is the next-day boundary and must be excluded.
- **Forecast history:** 578 WINDFOR records were retrieved. Each of the 24 hourly delivery times has multiple distinct `publishTime` values. All 24 hours have an eligible forecast at a minimum lead of 120 minutes; the latest eligible lead in this sample is 150 minutes.
- **Timestamp format:** ISO 8601 UTC, using `Z` or an explicit UTC offset.
- **Cutoff status:** `FORECAST_MIN_LEAD_MINUTES=120` remains the provisional technical rule. The blueprint's D-1 12:00 UTC policy requires clarification before it is finalized.
- **Fixtures:** `fuelhh_sample.json` and `windfor_sample.json` saved under `backend/tests/fixtures/`. The raw forecast history is also saved as `windfor_history_sample.json` for inspection.