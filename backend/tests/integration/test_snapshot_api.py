import json
from datetime import date

from app.services import snapshot

FAKE_RESULT = {
    "period": {"start": "2026-01-02", "end": "2026-02-01"},
    "timezone": "UTC",
    "forecast_cutoff": {"cutoff_utc": "09:50:00", "policy": "test policy"},
    "coverage": {"expected_hours": 744, "matched_hours": 1, "unmatched_hours": 743},
    "metrics": {"sample_count": 1, "mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0},
    "error_percentiles": {"p50": 10.0, "p90": 10.0, "p95": 10.0, "max": 10.0},
    "daily": [
        {"date": "2026-01-02", "sample_count": 1, "mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0}
    ],
    "hourly": [
        {"hour": 0, "sample_count": 1, "mae_mw": 10.0, "rmse_mw": 10.0, "bias_mw": 10.0}
    ],
    "matched_records": [
        {
            "startTime": "2026-01-02T00:00:00Z",
            "publishTime": "2026-01-01T09:30:00Z",
            "forecast_mw": 110.0,
            "actual_mw": 100.0,
        }
    ],
}


def _fake_analyse(start, end):
    return FAKE_RESULT


def test_build_snapshot_is_api_shaped_and_timestamped():
    data = snapshot.build_snapshot(
        date(2026, 1, 2), date(2026, 2, 1), analyse=_fake_analyse
    )

    assert data["points"] == FAKE_RESULT["matched_records"]
    assert "matched_records" not in data
    assert data["generated_at"].endswith("Z")
    assert data["metrics"] == FAKE_RESULT["metrics"]


def test_write_then_load_round_trips(tmp_path):
    path = tmp_path / "snap.json"
    data = snapshot.build_snapshot(
        date(2026, 1, 2), date(2026, 2, 1), analyse=_fake_analyse
    )

    snapshot.write_snapshot(data, path)

    assert snapshot.load_snapshot(path) == data


def test_snapshot_endpoint_serves_the_stored_file(client, monkeypatch, tmp_path):
    path = tmp_path / "snap.json"
    data = snapshot.build_snapshot(
        date(2026, 1, 2), date(2026, 2, 1), analyse=_fake_analyse
    )
    snapshot.write_snapshot(data, path)
    monkeypatch.setattr(snapshot, "SNAPSHOT_PATH", path)

    response = client.get("/api/v1/snapshot")

    assert response.status_code == 200
    body = response.json()
    assert body["generated_at"] == data["generated_at"]
    assert body["period"]["start"] == "2026-01-02"
    assert body["points"] == FAKE_RESULT["matched_records"]


def test_missing_snapshot_is_a_503_envelope(client, monkeypatch, tmp_path):
    monkeypatch.setattr(snapshot, "SNAPSHOT_PATH", tmp_path / "missing.json")

    response = client.get("/api/v1/snapshot")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "snapshot_unavailable"


def test_corrupt_snapshot_is_a_503_envelope(client, monkeypatch, tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(snapshot, "SNAPSHOT_PATH", path)

    response = client.get("/api/v1/snapshot")

    assert response.status_code == 503
    assert json.loads(response.text)["error"]["code"] == "snapshot_unavailable"