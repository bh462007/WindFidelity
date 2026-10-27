import httpx
import pandas as pd

url = "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type/wind-and-solar"

params = {
    "from": "2026-10-26T00:00:00Z",
    "to": "2026-10-26T03:00:00Z",
    "format": "json",
}

response = httpx.get(url, params=params, timeout=20)
response.raise_for_status()

data = response.json()
records = data["data"] if isinstance(data, dict) else data

df = pd.DataFrame(records)

# Keep wind records only
wind = df[df["businessType"] == "Wind generation"].copy()

# Combine onshore and offshore generation by timestamp
actuals = (
    wind.groupby("startTime", as_index=False)["quantity"]
    .sum()
    .rename(columns={"quantity": "actual_mw"})
)

print(actuals)