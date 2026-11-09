from app.ingestion.elexon_client import ElexonClient
from app.ingestion.schemas import validate_windfor_records


def test_stream_rows_without_settlement_fields_are_valid():
    row = {
        "dataset": "WINDFOR",
        "publishTime": "2026-01-14T09:30:00Z",
        "startTime": "2026-01-15T12:00:00Z",
        "generation": 8123.0,
    }

    result = validate_windfor_records([row])

    assert result["valid_records"] == [row]
    assert result["rejected_count"] == 0


def test_stream_rows_still_need_a_publish_time_and_generation():
    no_publish = {"startTime": "2026-01-15T12:00:00Z", "generation": 1.0}
    no_generation = {
        "publishTime": "2026-01-14T09:30:00Z",
        "startTime": "2026-01-15T12:00:00Z",
    }

    result = validate_windfor_records([no_publish, no_generation])

    assert result["valid_records"] == []
    assert result["rejected_count"] == 2


def test_fetch_windfor_stream_asks_for_a_publish_window_in_one_call():
    client = ElexonClient()
    calls = []

    def fake_fetch_json(endpoint, params):
        calls.append((endpoint, params))
        return [{"generation": 1}]

    client.fetch_json = fake_fetch_json

    rows = client.fetch_windfor_stream("2026-01-01T00:00:00Z", "2026-02-01T09:50:00Z")

    assert rows == [{"generation": 1}]
    assert calls == [
        (
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": "2026-01-01T00:00:00Z",
                "publishDateTimeTo": "2026-02-01T09:50:00Z",
                "format": "json",
            },
        )
    ]