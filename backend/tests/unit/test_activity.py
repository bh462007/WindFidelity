from datetime import datetime, timezone

from app.services.activity import ActivityLog

FIXED = datetime(2026, 11, 5, 12, 0, 0, tzinfo=timezone.utc)


def make_log(max_events=3):
    return ActivityLog(max_events=max_events, clock=lambda: FIXED)


def test_records_event_with_utc_timestamp_and_details():
    log = make_log()

    event = log.record("ingestion", "FUELHH loaded", rows=48)

    assert event == {
        "id": 1,
        "timestamp": "2026-11-05T12:00:00Z",
        "kind": "ingestion",
        "message": "FUELHH loaded",
        "details": {"rows": 48},
    }


def test_recent_returns_newest_first():
    log = make_log()
    log.record("cache", "first")
    log.record("cache", "second")

    assert [e["message"] for e in log.recent()] == ["second", "first"]


def test_ring_buffer_drops_oldest_events():
    log = make_log(max_events=3)
    for n in range(5):
        log.record("cache", f"event {n}")

    assert [e["message"] for e in log.recent()] == ["event 4", "event 3", "event 2"]


def test_ids_keep_increasing_after_events_are_dropped():
    log = make_log(max_events=2)
    for n in range(4):
        log.record("cache", f"event {n}")

    assert [e["id"] for e in log.recent()] == [4, 3]


def test_recent_respects_limit():
    log = make_log(max_events=10)
    for n in range(5):
        log.record("cache", f"event {n}")

    assert len(log.recent(limit=2)) == 2
    assert log.recent(limit=0) == []


def test_clear_empties_the_log():
    log = make_log()
    log.record("cache", "x")

    log.clear()

    assert log.recent() == []