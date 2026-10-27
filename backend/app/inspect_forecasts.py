import httpx
import pandas as pd

url = "https://data.elexon.co.uk/bmrs/api/v1/forecast/generation/wind/latest"

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

print("Columns:")
print(df.columns.tolist())

print("\nForecast records:")
print(df[["publishTime", "startTime", "generation"]].to_string(index=False))