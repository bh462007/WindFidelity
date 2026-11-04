# Day 5 Report — Frontend Dashboard


**Stack:** Vite 8, React, TypeScript, Recharts, oxlint

## Outcome

| Done-when item | Status |
|---|---|
| Both charts render from the live API | Done |
| Error state shows a retry button | Done |
| Empty state distinguishes "no data" from "unavailable" | Done |
| `npm run build` succeeds (types check) | Done |

## What was built

| File | Purpose |
|---|---|
| `src/api/client.ts` | Typed fetch client for `/api/v1/summary` and `/api/v1/timeseries`; sorts failures into `no_data`, `unavailable`, `invalid`, `unknown` |
| `src/hooks/useAnalysis.ts` | Loads summary then timeseries for a day; exposes loading / error / ready and a retry |
| `src/components/States.tsx` | Loading, "No data for this day", "That date isn't valid", "Data unavailable" with Retry |
| `src/components/SummaryCards.tsx` | MAE, RMSE, signed bias with a plain-words direction, coverage % |
| `src/components/GenerationChart.tsx` | Forecast vs actual lines (blue solid vs orange dashed) |
| `src/components/ErrorChart.tsx` | Forecast minus actual by hour, with a zero line |
| `src/App.tsx` | Shell with a date picker, default 2026-01-15 |

The dev server proxies `/api` to the backend on `127.0.0.1:8000`.

## Browser test (done by hand)

1. Happy path: loading, then cards and both charts.
2. Date with no data (2027-01-01): "No data for this day", no Retry button.
3. Backend stopped: "Data unavailable" with a Retry button.
4. Backend restarted, Retry clicked: data appears without a page reload.

## Design choices

- Summary and timeseries are fetched one after the other, so the backend computes a day once and serves the second request from its cache.
- Chart hours come from the UTC timestamp text, so the browser timezone cannot shift them.
- Chart lines differ in colour and in line style, so they do not rely on colour alone.
- The data request is cancelled when the date changes, so a slow earlier response cannot overwrite a newer one.

## Repository hygiene

- Template README, demo styles and demo assets were removed.
- `node_modules/` and `dist/` are ignored; the root `.gitignore` also covers `.env` and `.ruff_cache/`.

## Open issues

- The production bundle is about 590 kB because of Recharts, which triggers a build warning. Harmless for this app.
- The unavailable message reads "Request failed (502)"; friendlier wording would be better.
- The default date is hard-coded to 2026-01-15, not "latest available day".
- No frontend tests yet.
- The root `README.md` still does not exist.
- The positive forecast bias from Day 3 is still unexplained.