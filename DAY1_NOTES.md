# GridBricks — Day 1 Data Verification

- **Endpoints:** FUELHH: `/datasets/FUELHH/stream` using `settlementDateFrom` and `settlementDateTo`; WINDFOR: `/forecast/generation/wind/evolution` using `startTime`.
- **Actual generation:** Use FUELHH records with `fuelType = "WIND"`. The October 26, 2026 sample contains 48 half-hourly records. All 48 timestamps align with the existing actual wind endpoint; its additional timestamp is the next-day boundary and must be excluded.
- **Forecast history:** 578 WINDFOR records were retrieved for October 26, 2026. The 24 hourly delivery times have multiple distinct `publishTime` values. Forecast selection uses the latest publication at or before 12:00 UTC on the previous calendar day.
- **Timestamp format:** ISO 8601 UTC, using `Z` or an explicit UTC offset.
- **Cutoff status:** Fixed day-ahead cutoff selected: D-1 at 12:00 UTC. Configured through `FORECAST_CUTOFF_UTC`, defaulting to `12:00`. Forecasts published after the cutoff are excluded.
- **Fixtures:** `fuelhh_sample.json` and `windfor_sample.json` saved under `backend/tests/fixtures/`. The raw forecast history is also saved as `windfor_history_sample.json` for inspection.
- **Lead-time distribution (26 Oct 2026 sample):** Each delivery hour has 24–32 distinct `publishTime` values. Publication-to-delivery gaps range from about -25.5h (published after delivery) to +65.5h. Every hour has at least one vintage at or before D-1 12:00 UTC, so the cutoff leaves no hour without a forecast.
- **Jan 2026 availability (checked 30 Oct 2026):** 15 Jan 2026 FUELHH returned 48 WIND rows. WINDFOR for the 12:00 hour returned 24 records with 24 distinct `publishTime` values. Jan data is available, so Day 2 can proceed.