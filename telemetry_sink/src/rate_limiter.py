import asyncio
import time


class RateLimiter:
    def __init__(self, rate_limit_bytes_per_second: int):
        self._capacity = float(rate_limit_bytes_per_second)
        self._refill_rate = float(rate_limit_bytes_per_second)
        self._tokens = self._capacity
        self._last_refill_time = time.monotonic()

        self._lock = asyncio.Lock()

    def _refill(self):
        now = time.monotonic()
        elapsed_time = now - self._last_refill_time

        new_tokens = elapsed_time * self._refill_rate

        self._tokens = min(self._tokens + new_tokens, self._capacity)

        self._last_refill_time = now

    async def consume(self, num_bytes: int) -> bool:
        async with self._lock:
            self._refill()

            if num_bytes <= self._tokens:
                self._tokens -= num_bytes
                return True

        return False
