import json
from pathlib import Path

import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
START = "2026-10-26T00:00:00Z"
END = "2026-10-27T00:00:00Z"

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "tests" / "fixtures"

ENDPOINTS = {
    "actuals_sample.json": "/generation/actual/per-type/wind-and-solar",
    "windfor_sample.json": "/forecast/generation/wind/latest",
}


def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)

    for filename, endpoint in ENDPOINTS.items():
        url = f"{BASE_URL}{endpoint}"
        params = {
            "from": START,
            "to": END,
            "format": "json",
        }

        print(f"Fetching {filename}...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        output_path = FIXTURES / filename
        output_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        records = data.get("data", []) if isinstance(data, dict) else data
        print(f"Saved {len(records)} records to {output_path}")

        if records:
            print("First record:", records[0])
        else:
            print("WARNING: No records returned.")

    # Fetch forecast publication history for inspection
    history_url = f"{BASE_URL}/forecast/generation/wind/evolution"
    history_params = {
        "startTime": "2026-10-26T12:00:00Z",
        "format": "json",
    }

    print("Fetching wind forecast history...")
    response = requests.get(
        history_url,
        params=history_params,
        timeout=30,
    )
    response.raise_for_status()

    history = response.json()
    if isinstance(history, dict):
        history = history.get("data", [])

    history_path = FIXTURES / "windfor_history_sample.json"
    history_path.write_text(
        json.dumps(history, indent=2),
        encoding="utf-8",
    )
    print(f"Saved {len(history)} history records to {history_path}")

    from datetime import datetime

    def parse_utc(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    lead_times = []
    for row in history:
        published = row.get("publishTime")
        delivery = row.get("startTime")
        if not published or not delivery:
            continue

        minutes = (
            parse_utc(delivery) - parse_utc(published)
        ).total_seconds() / 60
        lead_times.append((published, delivery, minutes))

    lead_times.sort(key=lambda item: item[0])

    print(f"\nRecords with timestamps: {len(lead_times)}")
    print("\nPublication time | Delivery time | Lead time (hours)")
    for published, delivery, minutes in lead_times:
        print(f"{published} | {delivery} | {minutes / 60:.1f}")

    eligible = sum(minutes >= 120 for _, _, minutes in lead_times)
    print(f"\nRecords published at least 120 minutes ahead: {eligible}")

    print("\nSample fetching complete.")


if __name__ == "__main__":
    main()