import threading
from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self):
        self._buckets = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = monotonic()
        cutoff = now - window_seconds

        with self._lock:
            bucket = self._buckets[key]

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(now)
            return True


rate_limiter = InMemoryRateLimiter()


def rate_limit(scope: str, limit: int = 5, window_seconds: int = 60):
    def dependency(request: Request):
        client_key = request.client.host if request.client else "unknown"
        bucket_key = f"{scope}:{client_key}"

        if not rate_limiter.allow(bucket_key, limit, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

    return dependency
