import json
from time import sleep

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import (
    FixedPrefixRedisTestClient,
    IsolatedRedisTestClient,
)
from apps.core.utils.redis_repository import CacheRepository
from apps.qna.dtos import InitialQNA, Message


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
        CacheRepository.save_initial(self.key, self.data, ttl=5)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_initial_save(self) -> None:
        cashed = json.loads(cache.get(self.key))
        self.assertEqual(cashed, self.data)

    def test_initial_save_ttl(self) -> None:
        CacheRepository.save_initial(self.key, self.data, ttl=1)
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

    def test_save_history(self) -> None:
        history = [{"role": "user", "content": "hello"}]
        CacheRepository.save_history("history_key", history, ttl=5)
        cached = json.loads(cache.get("history_key"))
        self.assertEqual(cached, history)

    def test_get_history_returns_none_when_key_not_exists(self) -> None:
        self.assertIsNone(CacheRepository.get_history("nonexistent_key"))

    def test_get_history_returns_message_list(self) -> None:
        history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        CacheRepository.save_history("history_key", history, ttl=5)
        result = CacheRepository.get_history("history_key")
        self.assertIsInstance(result, list)
        assert result is not None
        self.assertIsInstance(result[0], Message)

    def test_set_session(self) -> None:
        CacheRepository.set_session("session_key", 42, ttl=5)
        cached = cache.get("session_key")
        self.assertEqual(cached, 42)

    def test_get_session_returns_none_when_key_not_exists(self) -> None:
        self.assertIsNone(CacheRepository.get_session("nonexistent_key"))

    def test_get_session_returns_int(self) -> None:
        CacheRepository.set_session("session_key", 42, ttl=5)
        result = CacheRepository.get_session("session_key")
        self.assertEqual(result, 42)
        self.assertIsInstance(result, int)


class TestCacheRepositoryGetQnaList(FixedPrefixRedisTestClient):

    def setUp(self) -> None:
        super().setUp()
        self.user_id = 1
        self.value = [
            {"role": "user", "content": "질문입니다.", "created_at": None},
            {"role": "assistant", "content": "답변입니다.", "created_at": "2026-04-23T14:30:05"},
        ]
        cache.set(f"qna_chat:{self.user_id}:42", self.value)
        cache.set(f"qna_chat:{self.user_id}:55", self.value)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_returns_qna_list(self) -> None:
        result = CacheRepository.get_qna_list(self.user_id)
        self.assertEqual(len(result), 2)

    def test_question_id_parsed(self) -> None:
        result = CacheRepository.get_qna_list(self.user_id)
        question_ids = {r.question_id for r in result}
        self.assertIn(42, question_ids)
        self.assertIn(55, question_ids)

    def test_last_message_is_last_item(self) -> None:
        result = CacheRepository.get_qna_list(self.user_id)
        for item in result:
            self.assertEqual(item.last_message, "답변입니다.")
            self.assertEqual(item.role, "assistant")

    def test_empty_when_no_keys(self) -> None:
        result = CacheRepository.get_qna_list(user_id=999)
        self.assertEqual(result, [])
