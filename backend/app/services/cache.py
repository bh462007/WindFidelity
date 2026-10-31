import time


class TTLCache:
    def __init__(self, ttl_seconds: float, clock=time.monotonic):
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._items = {}

    def get_or_compute(self, key, compute):
        hit = self._items.get(key)
        if hit is not None and self._clock() - hit[0] < self.ttl_seconds:
            return hit[1]

        value = compute()
        self._items[key] = (self._clock(), value)
        return value

    def clear(self):
        self._items.clear()