
import httpx
import pandas as pd
import numpy as np

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# 1. Fetch one historical forecast version.
forecast_response = httpx.get(
    f"{BASE_URL}/forecast/generation/wind/history",
    params={
        "publishTime": "2026-10-25T12:30:00Z",
        "format": "json",
    },
    timeout=20,
)
forecast_response.raise_for_status()

forecast_data = forecast_response.json()
forecast_records = (
    forecast_data.get("data", [])
    if isinstance(forecast_data, dict)
    else forecast_data
)

forecasts = pd.DataFrame(forecast_records)
forecasts["startTime"] = pd.to_datetime(
    forecasts["startTime"], utc=True
)
forecasts["publishTime"] = pd.to_datetime(
    forecasts["publishTime"], utc=True
)

forecasts = forecasts[
    (forecasts["startTime"] >= "2026-10-26T00:00:00Z")
    & (forecasts["startTime"] < "2026-10-27T00:00:00Z")
].copy()

forecasts = forecasts.rename(
    columns={"generation": "forecast_mw"}
)

# 2. Fetch actual wind generation.
actual_response = httpx.get(
    f"{BASE_URL}/generation/actual/per-type/wind-and-solar",
    params={
        "from": "2026-10-26T00:00:00Z",
        "to": "2026-10-27T00:00:00Z",
        "format": "json",
    },
    timeout=20,
)
actual_response.raise_for_status()

actual_data = actual_response.json()
actual_records = (
    actual_data.get("data", [])
    if isinstance(actual_data, dict)
    else actual_data
)

actuals = pd.DataFrame(actual_records)
actuals = actuals[
    actuals["businessType"] == "Wind generation"
].copy()

actuals["startTime"] = pd.to_datetime(
    actuals["startTime"], utc=True
)

# Exclude readings at the end boundary.
actuals = actuals[
    (actuals["startTime"] >= "2026-10-26T00:00:00Z")
    & (actuals["startTime"] < "2026-10-27T00:00:00Z")
]

# Combine onshore and offshore readings for each half-hour.
half_hourly = (
    actuals.groupby("startTime", as_index=False)["quantity"]
    .sum()
    .rename(columns={"quantity": "actual_mw"})
)

# Average the two half-hourly readings into each hour.
half_hourly["hour"] = half_hourly["startTime"].dt.floor("h")

hourly_actuals = (
    half_hourly.groupby("hour")
    .agg(
        actual_mw=("actual_mw", "mean"),
        readings=("actual_mw", "count"),
    )
    .reset_index()
)

# Keep only complete hours.
hourly_actuals = hourly_actuals[
    hourly_actuals["readings"] == 2
]

# 3. Match forecasts and actuals by delivery hour.
matched = forecasts.merge(
    hourly_actuals,
    left_on="startTime",
    right_on="hour",
    how="inner",
)

if matched.empty:
    raise ValueError("No matching forecast and actual records found.")

# 4. Calculate errors. Positive bias means overforecasting.
matched["error_mw"] = (
    matched["forecast_mw"] - matched["actual_mw"]
)

mae = matched["error_mw"].abs().mean()
rmse = np.sqrt((matched["error_mw"] ** 2).mean())
bias = matched["error_mw"].mean()

print("Matched hours:", len(matched))
print(f"MAE:  {mae:.2f} MW")
print(f"RMSE: {rmse:.2f} MW")
print(f"Bias: {bias:.2f} MW")

print("\nHourly comparison:")
print(
    matched[
        ["startTime", "forecast_mw", "actual_mw", "error_mw"]
    ].to_string(index=False)
)
