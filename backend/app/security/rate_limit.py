import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """In-memory sliding-window limiter, keyed by caller.

    Single-process only: acceptable for this app's current deployment shape.
    A multi-instance deployment would need a shared store (e.g. Redis) instead.
    """

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, max_hits: int, window_seconds: float) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= max_hits:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


auth_rate_limiter = RateLimiter()
