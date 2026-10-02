import time
from collections import defaultdict
from dataclasses import dataclass

from config import settings

_request_log: dict[str, list[float]] = defaultdict(list)


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded, retry after {retry_after_seconds} seconds")


@dataclass
class RateLimitRule:
    key_prefix: str
    max_requests: int
    window_seconds: int


SYNTHESIS_RULE = RateLimitRule(
    key_prefix="synthesis",
    max_requests=settings.tts_rate_limit_per_hour,
    window_seconds=3600,
)

PROFILE_CREATION_RULE = RateLimitRule(
    key_prefix="profile_creation",
    max_requests=settings.profile_creation_rate_limit_per_day,
    window_seconds=86400,
)


def check_rate_limit(user_id: str, rule: RateLimitRule) -> None:
    key = f"{rule.key_prefix}:{user_id}"
    now = time.time()
    window_start = now - rule.window_seconds

    timestamps = [t for t in _request_log[key] if t > window_start]
    _request_log[key] = timestamps

    if len(timestamps) >= rule.max_requests:
        oldest = min(timestamps)
        retry_after = int(oldest + rule.window_seconds - now)
        raise RateLimitExceeded(retry_after_seconds=max(retry_after, 1))

    timestamps.append(now)
    _request_log[key] = timestamps