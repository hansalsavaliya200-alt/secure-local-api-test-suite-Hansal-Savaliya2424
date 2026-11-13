"""In-memory sliding-window rate limiter. The clock is injectable so tests need no sleeping."""
import math
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._hits = defaultdict(deque)

    def check(self, key: str, limit: tuple):
        """Return (allowed, retry_after_seconds)."""
        max_requests, window = limit
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= window:
            hits.popleft()
        if len(hits) >= max_requests:
            return False, max(1, math.ceil(window - (now - hits[0])))
        hits.append(now)
        return True, 0
