import httpx

url = "https://data.elexon.co.uk/bmrs/api/v1/generation/actual/per-type/wind-and-solar"

params = {
    "from": "2026-10-26T00:00:00Z",
    "to": "2026-10-26T03:00:00Z",
    "format": "json",
}

response = httpx.get(url, params=params, timeout=20)

print("Status code:", response.status_code)

response.raise_for_status()

data = response.json()

print("Response received successfully!")

if isinstance(data, dict):
    records = data.get("data", [])
else:
    records = data

print("Number of records:", len(records))
print("First three records:")

for record in records[:3]:
    print(record)