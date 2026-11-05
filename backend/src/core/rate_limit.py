import time
from collections import defaultdict, deque
from typing import Deque, Dict
from fastapi import Depends
from src.core.auth import AuthUser, get_current_user
from src.core.config import get_settings
from src.core.errors import FDISException

_hits: Dict[str, Deque[float]] = defaultdict(deque)


class RateLimitError(FDISException):
    def __init__(self):
        super().__init__(
            title="Too Many Requests",
            detail="Rate limit reached. Try again in a minute.",
            status_code=429,
            code="rate_limited",
        )


def reset_rate_limits() -> None:
    _hits.clear()


async def rate_limited_user(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Authenticated user, limited per minute. In-memory: per process, resets on restart."""
    limit = get_settings().RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return user
    now = time.monotonic()
    q = _hits[user.id]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise RateLimitError()
    q.append(now)
    return user
