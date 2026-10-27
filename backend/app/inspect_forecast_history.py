
import httpx
import pandas as pd

url = "https://data.elexon.co.uk/bmrs/api/v1/forecast/generation/wind/history"

params = {
    "publishTime": "2026-10-25T12:30:00Z",
    "format": "json",
}

response = httpx.get(url, params=params, timeout=20)
response.raise_for_status()

data = response.json()
records = data.get("data", []) if isinstance(data, dict) else data

df = pd.DataFrame(records)


df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
df["startTime"] = pd.to_datetime(df["startTime"], utc=True)

# Keep forecasts published before their delivery period starts.
usable = df[df["publishTime"] < df["startTime"]].copy()

print("\nUsable forecast records:", len(usable))
print("\nFirst usable records:")
print(
    usable[["publishTime", "startTime", "generation"]]
    .head(10)
    .to_string(index=False)
)

print("\nForecasts for October 26:")
oct26 = usable[
    usable["startTime"].dt.strftime("%Y-%m-%d") == "2026-10-26"
]
print(oct26[["publishTime", "startTime", "generation"]].to_string(index=False))


print("Total records:", len(df))
print("\nAvailable columns:")
print(df.columns.tolist())

print("\nUnique publication times:")
print(df["publishTime"].drop_duplicates().to_list())

print("\nForecast time range:")
print("First:", df["startTime"].min())
print("Last:", df["startTime"].max())

print("\nSample records:")
print(df[["publishTime", "startTime", "generation"]].head(10).to_string(index=False))
