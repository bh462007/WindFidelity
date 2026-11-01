# Day 3 Report — Match + Metrics

**Tests:** 59 passing

## Outcome

| Done-when item | Status |
|---|---|
| All four cutoff tests pass | Done |
| MAE / RMSE / bias match a hand-computed fixture | Done (3-row fixture) |
| API returns real numbers, not 503 | Done, at `/api/v1/metrics?day=YYYY-MM-DD` (not `/api/summary`) |
| Explain the cutoff rule in 30 seconds | Yours to rehearse; reference answer below |

## Pipeline output (Jan 2026, real Elexon data)

| Day | Matched | Unmatched | MAE (MW) | Bias (MW) |
|---|---|---|---|---|
| 5 Jan | 24 | 0 | 861 | +219 |
| 10 Jan | 24 | 0 | 1,245 | +856 |
| 15 Jan | 24 | 0 | 1,190 | +1,190 |
| 20 Jan | 24 | 0 | 1,029 | +318 |
| 25 Jan | 24 | 0 | 1,735 | +1,735 |

Mean bias across the five days: about +864 MW (forecast above actual).

## Cutoff rule (30-second version)

For each delivery hour, use the latest forecast published at or before 12:00 UTC on the previous calendar day. A forecast published exactly at the cutoff is kept; one published a second later is rejected. If no forecast qualifies, that hour is unmatched. This stops later information leaking into the forecast being scored.

## Cutoff tests

- Forecast published after the cutoff is rejected.
- Earlier forecast is selected; the latest eligible one wins.
- Forecast published exactly at the cutoff is selected.
- No candidate at or before the cutoff returns nothing.
- Forecast published after delivery is excluded.

## Surprises and fixes

1. **Wrong actuals source.** The service used the per-type wind-and-solar endpoint, which reports onshore and offshore as separate rows. Keep-last dedupe then dropped onshore, so actuals were offshore only (hour 00:00 on 26 Oct: 10,377 MW against 14,847 MW from FUELHH). This inflated the old bias (+2,421 MW). Fixed by switching to FUELHH WIND, as the Day 1 notes had chosen.
2. **Crash in matching.** `match.parse_timestamp` assumed strings, but cleaned actuals carry `datetime` objects. The mocked tests hid it. Fixed, with a regression test using a real datetime.
3. **Order-dependent test.** A test assumed forecast calls arrive in hour order, but they run in a 6-thread pool. It now compares sorted hours.

## Additions beyond the original plan

- `coverage` in the response: expected, matched and unmatched hours.
- `TTLCache` (300 s, keyed by day, exceptions are not cached). Measured: first request 1.89 s, repeat 0.01 s.

## Deviations from the plan

- Route is `/api/v1/metrics`, not `/api/summary`.
- Selection function is `select_forecast_vintages`, not `select_forecast`.
- Coverage % metric was not built (first in the cut order).
- Matching works on hourly means, since WINDFOR is hourly.

## Open issues

- **Unexplained positive bias.** The forecast was above actual on average on all five days. Cause unknown: could be genuine forecast bias, or WINDFOR and FUELHH WIND may not measure exactly the same wind. Five days cannot separate these.
- `backend/reports/sample_evaluation.json` was produced with the old offshore-only actuals and is stale.
- `ElexonClient.fetch_windfor` returns unvalidated rows (validation currently happens in `analysis_service`).
- Retry backoff uses urllib3's `backoff_factor=1`, which may not be exactly 1/2/4 s.

## Next

- Regenerate or remove the stale sample evaluation report.
- Investigate the bias over a longer window (a full month) and check how WINDFOR and FUELHH WIND are defined.