"""
Simple in-memory TTL cache for Cymor Movie Hub.
Keeps Render free tier happy by reducing redundant upstream calls.
"""

import time
import asyncio
from typing import Any, Optional
import logging

logger = logging.getLogger("cymor.cache")


class TTLCache:
    """
    Thread-safe in-memory TTL cache.
    Default TTL: 10 minutes for search results, 30 minutes for details.
    """

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._store:
                value, expires_at = self._store[key]
                if time.time() < expires_at:
                    logger.debug(f"Cache HIT: {key}")
                    return value
                else:
                    del self._store[key]
                    logger.debug(f"Cache EXPIRED: {key}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 600):
        """Store a value with TTL in seconds (default 10 min)."""
        async with self._lock:
            self._store[key] = (value, time.time() + ttl)
            logger.debug(f"Cache SET: {key} (TTL={ttl}s)")

    async def delete(self, key: str):
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self):
        async with self._lock:
            self._store.clear()
            logger.info("Cache cleared.")

    def stats(self) -> dict:
        now = time.time()
        active = sum(1 for _, (_, exp) in self._store.items() if now < exp)
        return {"total_keys": len(self._store), "active_keys": active}


# Singleton cache instance
cache = TTLCache()
