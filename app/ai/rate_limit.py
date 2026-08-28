from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, status

_events: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def enforce_ai_rate_limit(key: str, *, requests: int = 20, window_seconds: int = 60) -> None:
    """Bound costly AI operations per authenticated user and feature."""
    now = monotonic()
    with _lock:
        events = _events[key]
        while events and events[0] <= now - window_seconds:
            events.popleft()
        if len(events) >= requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Aria request limit reached. Try again shortly.")
        events.append(now)


def reset_ai_rate_limits() -> None:
    with _lock:
        _events.clear()
