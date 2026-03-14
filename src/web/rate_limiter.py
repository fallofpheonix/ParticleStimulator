"""Simple in-memory sliding-window rate limiter for the HTTP API."""
from __future__ import annotations

import time
from collections import deque
from threading import Lock


class RateLimiter:
    """Sliding-window rate limiter keyed by an arbitrary client identifier (e.g. IP address).

    Each client is allowed at most *max_requests* calls within any rolling
    *window_seconds* interval.  Older timestamps outside the window are
    discarded on each check, so memory consumption is bounded by
    ``O(max_requests)`` per active client.
    """

    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._max = max_requests
        self._window = window_seconds
        self._lock = Lock()
        self._buckets: dict[str, deque[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Return *True* and record the request if the client is within the limit.

        Return *False* without recording if the client has already reached
        the maximum number of requests for the current window.
        """
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            bucket = self._buckets.setdefault(client_id, deque())
            # Discard timestamps that have fallen outside the current window.
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max:
                return False
            bucket.append(now)
            return True

    def purge_stale(self) -> None:
        """Remove records for clients that have been inactive for a full window.

        Call periodically to reclaim memory when the number of distinct
        client IPs is large.
        """
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            stale = [k for k, ts in self._buckets.items() if not ts or ts[-1] < cutoff]
            for k in stale:
                del self._buckets[k]
