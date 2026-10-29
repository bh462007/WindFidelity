# Actual-generation raw-response provenance

Status: not yet captured.

Endpoint:
- https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type/wind-and-solar

Request parameters:
- from: 2026-10-26T00:00:00Z
- to: 2026-10-27T00:00:00Z
- format: json

Output path:
- backend/tests/fixtures/actuals_raw_response.json

Capture timestamp:
- not captured yet; fill this in only when the live request is executed.

Purpose:
- Preserve the complete raw Elexon response object without stripping the top-level `data` wrapper, while leaving the existing fixture at backend/tests/fixtures/actuals_sample.json unchanged.
