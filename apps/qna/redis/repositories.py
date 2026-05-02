import json

from django.core.cache import cache

from apps.qna.redis.dtos import InitialQNA


class CacheRepository:
    @staticmethod
    def initial_save(key: str, value: dict) -> None:
        cache.set(key, json.dumps(value))

    @staticmethod
    def get(key: str) -> InitialQNA | None:
        cached = cache.get(key)
        if not cached:
            return None
        return InitialQNA(**json.loads(cached))