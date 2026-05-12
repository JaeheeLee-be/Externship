import json
from time import sleep

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.qna.redis import CacheRepository
from apps.qna.redis.dtos import InitialQNA


class TestCacheRepository(IsolatedRedisTestClient):

    def setUp(self) -> None:
        super().setUp()

        self.data = {
            "category": "cat",
            "title": "title",
            "content": "content",
            "answer": "answer",
            "question_id": 1,
            "using_model": "model",
            "created_at": "2026-05-04",
        }
        self.key = "key"
        CacheRepository.initial_save(self.key, self.data, ttl=5)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_initial_save(self) -> None:
        cashed = json.loads(cache.get(self.key))
        self.assertEqual(cashed, self.data)

    def test_initial_save_ttl(self) -> None:
        CacheRepository.initial_save(self.key, self.data, ttl=1)
        sleep(1.5)
        self.assertIsNone(CacheRepository.get_initial(self.key))

    def test_get_returns_none_when_key_not_exists(self) -> None:
        self.assertIsNone(CacheRepository.get_initial("nonexistent_key"))

    def test_get_returns_InitialQNA(self) -> None:
        self.assertIsInstance(CacheRepository.get_initial(self.key), InitialQNA)

    def test_acquire_lock_returns_true_first_time(self) -> None:
        self.assertTrue(CacheRepository.acquire_lock("lock_key"))

    def test_acquire_lock_returns_false_if_already_locked(self) -> None:
        CacheRepository.acquire_lock("lock_key")
        self.assertFalse(CacheRepository.acquire_lock("lock_key"))

    def test_get_returns_none_after_delete(self) -> None:
        CacheRepository.delete(self.key)
        self.assertIsNone(CacheRepository.get_initial(self.key))
