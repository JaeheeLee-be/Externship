import json
from typing import Any

from django.core.cache import cache

from apps.qna.redis.dtos import InitialQNA


class CacheRepository:
    @staticmethod
    def initial_save(key: str, value: dict[str, Any], ttl: int) -> None:
        cache.set(key, json.dumps(value), timeout=ttl)

    @staticmethod
    def get_initial(key: str) -> InitialQNA | None:
        cached = cache.get(key)
        if not cached:
            return None
        return InitialQNA(**json.loads(cached))

    @staticmethod
    def acquire_lock(key: str) -> bool:
        return cache.add(key, "1", timeout=60)

    @staticmethod
    def delete(key: str) -> None:
        cache.delete(key)
