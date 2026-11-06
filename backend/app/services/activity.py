from collections import deque
from datetime import datetime, timezone
from threading import Lock


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ActivityLog:
    """In-memory ring buffer of real pipeline events. Read-only to API clients."""

    def __init__(self, max_events: int = 100, clock=_utc_now):
        self.max_events = max_events
        self._clock = clock
        self._events = deque(maxlen=max_events)
        self._next_id = 1
        self._lock = Lock()

    def record(self, kind: str, message: str, **details) -> dict:
        with self._lock:
            event = {
                "id": self._next_id,
                "timestamp": self._clock().isoformat().replace("+00:00", "Z"),
                "kind": kind,
                "message": message,
                "details": details,
            }
            self._next_id += 1
            self._events.append(event)
            return event

    def recent(self, limit: int = 50) -> list[dict]:
        if limit <= 0:
            return []
        with self._lock:
            items = list(self._events)
        return list(reversed(items[-limit:]))

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


activity_log = ActivityLog()