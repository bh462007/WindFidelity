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

    # Fetch forecast evolution for each delivery hour
    from datetime import datetime, timedelta

    history_url = f"{BASE_URL}/forecast/generation/wind/evolution"

    start_dt = datetime.fromisoformat(START.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(END.replace("Z", "+00:00"))

    history = []
    delivery = start_dt

    while delivery < end_dt:
        params = {
            "startTime": delivery.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "format": "json",
        }
        response = requests.get(history_url, params=params, timeout=30)
        response.raise_for_status()

        records = response.json()
        if isinstance(records, dict):
            records = records.get("data", [])

        history.extend(records)
        delivery += timedelta(hours=1)

    history_path = FIXTURES / "windfor_history_sample.json"
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    # Select the latest vintage published at least 120 minutes before delivery
    by_delivery = {}
    for row in history:
        published = row.get("publishTime")
        target = row.get("startTime")
        if not published or not target:
            continue

        published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        target_dt = datetime.fromisoformat(target.replace("Z", "+00:00"))

        if (target_dt - published_dt).total_seconds() >= 120 * 60:
            by_delivery.setdefault(target, []).append(row)

    print(f"\nHistory records saved: {len(history)}")
    print(f"Delivery hours with an eligible vintage: {len(by_delivery)}")
    print("\nDelivery time | Selected publication time | Lead hours")

    for target in sorted(by_delivery):
        selected = max(by_delivery[target], key=lambda row: row["publishTime"])
        lead_hours = (
            datetime.fromisoformat(target.replace("Z", "+00:00"))
            - datetime.fromisoformat(
                selected["publishTime"].replace("Z", "+00:00")
            )
        ).total_seconds() / 3600
        print(f"{target} | {selected['publishTime']} | {lead_hours:.1f}")

    print("\nSample fetching complete.")


if __name__ == "__main__":
    main()