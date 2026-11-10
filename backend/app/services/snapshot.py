import json
from datetime import date, datetime, timezone
from pathlib import Path

from app.services.analysis_service import analyse_period

SNAPSHOT_PATH = Path(__file__).resolve().parents[2] / "data" / "january_2026.json"


class SnapshotUnavailable(Exception):
    """The stored snapshot is missing or unreadable."""


def build_snapshot(start: date, end: date, analyse=analyse_period) -> dict:
    """Run the live pipeline once and shape the result like the API response."""
    result = analyse(start, end)
    body = {key: value for key, value in result.items() if key != "matched_records"}

    return {
        **body,
        "points": result["matched_records"],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_snapshot(data: dict, path: Path | None = None) -> None:
    target = Path(path or SNAPSHOT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_snapshot(path: Path | None = None) -> dict:
    source = Path(path or SNAPSHOT_PATH)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotUnavailable(f"Snapshot not available: {exc}") from exc