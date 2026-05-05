"""
Lightweight in-memory rate limiter for login endpoint.
Works for single-instance deployments. Use Redis for multi-worker production.
"""
import time
import asyncio
from collections import defaultdict

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60  # 15 phút


class RateLimiter:
    """
    Track failed login attempts per IP.
    lockout = { ip: (attempt_count, first_attempt_timestamp) }
    """

    def __init__(self) -> None:
        self._attempts: dict[str, tuple[int, float]] = defaultdict(
            lambda: (0, 0.0)
        )
        self._lock = asyncio.Lock()

    async def is_locked(self, ip: str) -> bool:
        count, timestamp = self._attempts[ip]
        if count < MAX_ATTEMPTS:
            return False
        elapsed = time.time() - timestamp
        if elapsed >= WINDOW_SECONDS:
            # Window expired — reset
            async with self._lock:
                self._attempts[ip] = (0, 0.0)
            return False
        return True

    async def record_failure(self, ip: str) -> None:
        async with self._lock:
            count, timestamp = self._attempts[ip]
            if count == 0:
                # First failure in window
                async with self._lock:
                    self._attempts[ip] = (1, time.time())
            else:
                async with self._lock:
                    self._attempts[ip] = (count + 1, timestamp)

    async def reset(self, ip: str) -> None:
        """Reset on successful login."""
        async with self._lock:
            self._attempts[ip] = (0, 0.0)

    def ttl_remaining(self, ip: str) -> int:
        """Seconds until lockout expires. Returns 0 if not locked."""
        count, timestamp = self._attempts[ip]
        if count < MAX_ATTEMPTS:
            return 0
        elapsed = time.time() - timestamp
        remaining = WINDOW_SECONDS - elapsed
        return max(0, int(remaining))


login_limiter = RateLimiter()