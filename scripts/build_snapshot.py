"""Build the committed January 2026 snapshot from live Elexon data.

Run from anywhere:  python scripts/build_snapshot.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.snapshot import SNAPSHOT_PATH, build_snapshot, write_snapshot  # noqa: E402


def main() -> None:
    # Delivery days 2 Jan to 1 Feb 2026: purchase decisions made in January.
    data = build_snapshot(date(2026, 1, 2), date(2026, 2, 1))
    write_snapshot(data)

    metrics = data["metrics"]
    print(
        f"Wrote {SNAPSHOT_PATH}\n"
        f"  hours matched: {data['coverage']['matched_hours']}\n"
        f"  MAE {metrics['mae_mw']:.1f}  RMSE {metrics['rmse_mw']:.1f}  "
        f"bias {metrics['bias_mw']:+.1f} MW\n"
        f"  generated at {data['generated_at']}"
    )


if __name__ == "__main__":
    main()