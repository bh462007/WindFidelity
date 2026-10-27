
import json
from pathlib import Path

from app.processing.clean import aggregate_hourly_actuals
from app.processing.match import match_forecasts_to_actuals
from app.processing.metrics import calculate_metrics


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "backend" / "tests" / "fixtures"
REPORTS = ROOT / "backend" / "reports"


def load_json(filename):
    path = FIXTURES / filename
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, dict):
        data = data.get("data", [])

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {filename}")

    return data


def main():
    forecasts = load_json("windfor_history_sample.json")
    actual_records = load_json("actuals_sample.json")

    actuals = aggregate_hourly_actuals(actual_records)
    matched = match_forecasts_to_actuals(forecasts, actuals)

    print(f"Forecast history records: {len(forecasts)}")
    print(f"Complete hourly actuals: {len(actuals)}")
    print(f"Matched evaluation hours: {len(matched)}")

    if not matched:
        raise ValueError("No matched records; cannot evaluate accuracy.")

    metrics = calculate_metrics(matched)

    REPORTS.mkdir(parents=True, exist_ok=True)
    report = {
        "period_start": matched[0]["startTime"],
        "period_end": matched[-1]["startTime"],
        "minimum_lead_minutes": 120,
        "metrics": metrics,
        "matched_records": matched,
    }

    output = REPORTS / "sample_evaluation.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nAccuracy metrics:")
    for name, value in metrics.items():
        print(f"{name}: {value}")

    print(f"\nReport saved to: {output}")


if __name__ == "__main__":
    main()
