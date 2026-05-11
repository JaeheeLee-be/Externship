import json
from typing import Any, cast

from django.core.cache import cache
from django_redis import get_redis_connection  # type: ignore

from apps.qna.dtos import InitialQNA, LastQNAHistory, Message
from apps.qna.redis import CacheFactory


class CacheRepository:
    @staticmethod
    def save_initial(key: str, value: dict[str, Any], ttl: int) -> None:
        cache.set(key, json.dumps(value), timeout=ttl)

    @staticmethod
    def get_initial(key: str) -> InitialQNA | None:
        cached = cache.get(key)
        if not cached:
            return None
        return InitialQNA(**json.loads(cached))

    @staticmethod
    def get_history(key: str) -> list[Message] | None:
        cached = cache.get(key)
        if not cached:
            return None
        return [Message(**m) for m in json.loads(cached)]

    @staticmethod
    def save_history(key: str, history: list[dict[str, str]], ttl: int) -> None:
        cache.set(key, json.dumps(history), timeout=ttl)

    @staticmethod
    def acquire_lock(key: str, ttl: int = 60) -> bool:
        return cache.add(key, "1", timeout=ttl)

    @staticmethod
    def delete(key: str) -> None:
        cache.delete(key)

    @staticmethod
    def set_session(key: str, value: int, ttl: int) -> None:
        cache.set(key, value, timeout=ttl)

    @staticmethod
    def get_session(key: str) -> None | int:
        cached = cache.get(key)
        return cached if isinstance(cached, int) else None

    @staticmethod
    def get_qna_list(user_id: int) -> list[LastQNAHistory]:
        qna_list = []
        redis_client = get_redis_connection("default")
        for key in redis_client.scan_iter(match=f":1:qna_chat:{user_id}:*"):
            key = key.decode("utf-8").removeprefix(":1:")
            value = cache.get(key)
            if value is None:
                continue
            qna_list.append(CacheFactory.create_last_qna(key, value))
        return qna_list
