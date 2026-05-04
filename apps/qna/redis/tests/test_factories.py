from django.test import TestCase

from apps.qna.redis import CacheFactory
from apps.qna.redis.dtos import InitialQNA


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