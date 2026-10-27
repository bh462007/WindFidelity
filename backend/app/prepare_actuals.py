
import httpx
import pandas as pd

url = "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type/wind-and-solar"

params = {
    "from": "2026-10-26T00:00:00Z",
    "to": "2026-10-27T00:00:00Z",
    "format": "json",
}

response = httpx.get(url, params=params, timeout=20)
response.raise_for_status()

data = response.json()
records = data.get("data", []) if isinstance(data, dict) else data

df = pd.DataFrame(records)

# Keep wind generation only, excluding solar.
wind = df[df["businessType"] == "Wind generation"].copy()

wind["startTime"] = pd.to_datetime(wind["startTime"], utc=True)

# Combine onshore and offshore generation for each half-hour.
half_hourly = (
    wind.groupby("startTime", as_index=False)["quantity"]
    .sum()
    .rename(columns={"quantity": "actual_mw"})
)

# Group the two half-hourly readings into each hour.
half_hourly["hour"] = half_hourly["startTime"].dt.floor("h")

hourly = (
    half_hourly.groupby("hour")
    .agg(
        actual_mw=("actual_mw", "mean"),
        half_hour_readings=("actual_mw", "count"),
    )
    .reset_index()
)

print("Half-hourly records:", len(half_hourly))
print("\nHourly actuals:")
print(hourly.to_string(index=False))

print("\nHours without both half-hourly readings:")
print(hourly[hourly["half_hour_readings"] != 2].to_string(index=False))
