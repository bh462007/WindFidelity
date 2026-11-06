from app.services.activity import activity_log


def test_activity_is_empty_before_anything_happens(client):
    response = client.get("/api/v1/activity")

    assert response.status_code == 200
    assert response.json()["events"] == []
    assert response.json()["capacity"] == activity_log.max_events


def test_activity_returns_recorded_events_newest_first(client):
    activity_log.record("ingestion", "FUELHH loaded", rows=48)
    activity_log.record("match", "24 of 24 hours matched", matched_hours=24)

    events = client.get("/api/v1/activity").json()["events"]

    assert [e["kind"] for e in events] == ["match", "ingestion"]
    assert events[1]["details"] == {"rows": 48}


def test_activity_limit_is_applied(client):
    for n in range(5):
        activity_log.record("cache", f"event {n}")

    response = client.get("/api/v1/activity", params={"limit": 2})

    assert len(response.json()["events"]) == 2


def test_activity_rejects_out_of_range_limit(client):
    response = client.get("/api/v1/activity", params={"limit": 0})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"