import json
import hashlib
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    value = await r.get(key)
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value, default=str))


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        await r.delete(*keys)


def make_cache_key(*parts: Any) -> str:
    """Generate a deterministic cache key from parts."""
    raw = ":".join(str(p) for p in parts)
    return f"screener:{hashlib.md5(raw.encode()).hexdigest()}"


def make_screener_cache_key(filters: list, logic: str, exchange: list,
                             sort_by: str, sort_order: str, page: int, per_page: int) -> str:
    payload = {
        "filters": filters,
        "logic": logic,
        "exchange": sorted(exchange),
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
        "per_page": per_page,
    }
    raw = json.dumps(payload, sort_keys=True)
    return f"screener:run:{hashlib.md5(raw.encode()).hexdigest()}"
