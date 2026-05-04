from django.test import TestCase

from apps.qna.redis import CacheFactory
from apps.qna.redis.dtos import InitialQNA


class TestCacheFactory(TestCase):

    def test_create_initial_cache(self) -> None:
        result = CacheFactory.create_initial_cache(
            category="Python",
            title="테스트 제목",
            content="테스트 내용",
            answer="테스트 답변",
            question_id=1,
            using_model="gpt-4",
        )

        assert isinstance(result, InitialQNA)
        assert result.category == "Python"
        assert result.created_at is not None
