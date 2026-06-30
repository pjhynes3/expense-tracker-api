from typing import Any, Optional

_cache_store = {}


def cache_get(key: str) -> Optional[Any]:
    return _cache_store.get(key)


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    _cache_store[key] = value


def cache_delete(key: str) -> None:
    _cache_store.pop(key, None)


def cache_clear() -> None:
    _cache_store.clear()