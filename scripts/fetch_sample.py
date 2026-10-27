
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import requests

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
START = "2026-10-26T00:00:00Z"
END = "2026-10-27T00:00:00Z"

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "tests" / "fixtures"


def fetch(endpoint: str, params: dict) -> list[dict]:
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    if isinstance(data, dict):
        data = data.get("data", [])

    if not isinstance(data, list):
        raise ValueError(f"Unexpected response format from {url}")

    print(f"URL: {response.url}")
    print(f"Records: {len(data)}")
    if data:
        print("First record:", data[0])

    return data


def save_json(filename: str, data: list[dict]) -> None:
    path = FIXTURES / filename
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved {len(data)} records to {path}")


def main():
    FIXTURES.mkdir(parents=True, exist_ok=True)

    date_params = {
        "from": START,
        "to": END,
        "format": "json",
    }

    print("\n--- FUELHH: half-hourly generation outturn ---")
    fuelhh = fetch(
        "/datasets/FUELHH",
        {
            "settlementDateFrom": START[:10],
            "settlementDateTo": START[:10],
            "format": "json",
        },
    )
    
    save_json("fuelhh_sample.json", fuelhh)

    print("\n--- Actual wind and solar data (comparison sample) ---")
    actuals = fetch(
        "/generation/actual/per-type/wind-and-solar",
        date_params,
    )
    save_json("actuals_sample.json", actuals)

    print("\n--- WINDFOR forecast evolution ---")
    start_dt = datetime.fromisoformat(START.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(END.replace("Z", "+00:00"))

    history = []
    delivery = start_dt

    while delivery < end_dt:
        records = fetch(
            "/forecast/generation/wind/evolution",
            {
                "startTime": delivery.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "format": "json",
            },
        )
        history.extend(records)
        delivery += timedelta(hours=1)

    save_json("windfor_sample.json", history)
    save_json("windfor_history_sample.json", history)

    by_delivery = defaultdict(list)
    for row in history:
        published = row.get("publishTime")
        target = row.get("startTime")
        if not published or not target:
            continue

        published_dt = datetime.fromisoformat(
            published.replace("Z", "+00:00")
        )
        target_dt = datetime.fromisoformat(
            target.replace("Z", "+00:00")
        )

        by_delivery[target].append((published_dt, target_dt, row))

    print("\n--- Publication-time inspection ---")
    print("Delivery time | Distinct publications | Eligible at 120 min")
    eligible_hours = 0

    for target in sorted(by_delivery):
        entries = by_delivery[target]
        distinct = {item[0] for item in entries}
        eligible = [
            item for item in entries
            if (item[1] - item[0]).total_seconds() >= 120 * 60
        ]

        if eligible:
            eligible_hours += 1

        print(f"{target} | {len(distinct)} | {len(eligible)}")

        if eligible:
            selected = max(eligible, key=lambda item: item[0])
            lead_minutes = (
                selected[1] - selected[0]
            ).total_seconds() / 60
            print(
                f"  Latest eligible: {selected[0].isoformat()} "
                f"| lead: {lead_minutes:.0f} minutes"
            )

    print(f"\nTotal forecast records: {len(history)}")
    print(f"Delivery hours with eligible vintages: {eligible_hours}")
    print("Timestamp expectation: ISO 8601 with UTC offset or Z.")
    print("Sample fetching complete.")


if __name__ == "__main__":
    main()
