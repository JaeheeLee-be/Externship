from django.test import TestCase

from apps.qna.dtos import InitialQNA
from apps.qna.redis import CacheFactory


class TestCacheFactory(TestCase):

    def test_create_initial_cache(self) -> None:
        result = CacheFactory.create_initial_cache(
            category="test_category",
            title="test_title",
            content="test_content",
            answer="test_answer",
            question_id=1,
            using_model="test_model",
        )

        self.assertIsInstance(result, InitialQNA)
        self.assertEqual(result.category, "test_category")
        self.assertEqual(result.title, "test_title")
        self.assertEqual(result.content, "test_content")
        self.assertEqual(result.answer, "test_answer")
        self.assertEqual(result.question_id, 1)
        self.assertEqual(result.using_model, "test_model")
        self.assertIsNotNone(result.created_at)
        self.assertIsInstance(result.created_at, str)

    def test_create_qna_list(self) -> None:
        key = "qna_chat:1:42"
        value = [
            {"role": "user", "content": "질문입니다.", "created_at": None},
            {"role": "assistant", "content": "답변입니다.", "created_at": "2026-04-23T14:30:05"},
        ]
        result = CacheFactory.create_last_qna(key, value)
        self.assertEqual(result.question_id, 42)
        self.assertEqual(result.last_message, "답변입니다.")
        self.assertEqual(result.role, "assistant")
        self.assertEqual(result.created_at, "2026-04-23T14:30:05")
