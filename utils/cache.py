"""TTL in-memory cache for Cymor Movie Hub."""
import time, asyncio
from typing import Any, Optional

class TTLCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._store:
                value, expires = self._store[key]
                if time.time() < expires:
                    return value
                del self._store[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 600):
        async with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def stats(self):
        now = time.time()
        return {"keys": sum(1 for _, (_, e) in self._store.items() if now < e)}

cache = TTLCache()
