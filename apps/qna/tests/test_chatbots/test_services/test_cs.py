from dataclasses import asdict
from unittest.mock import MagicMock, patch

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import FixedPrefixRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.qna.dtos import Message
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import CS_KEY
from apps.qna.services.chatbot_cs import CSChatbotService


class TestCSChatbotService(FixedPrefixRedisTestClient):
    user_id: int = 1
    lines: list[str]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.lines = Res.make_lines()

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_iter_res(self.lines)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_response_cs_history_returns_existing_history(self) -> None:
        history = [
            Message(role="user", content="질문입니다."),
            Message(role="assistant", content="답변입니다."),
        ]
        CacheRepository.save_history(
            key=CS_KEY.format(user_id=self.user_id),
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        result = CSChatbotService.response_cs_history(self.user_id)
        self.assertEqual(len(result), 2)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_cs_chat_streams_and_saves_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = list(CSChatbotService.response_cs_chat(self.user_id, None, "질문입니다."))
        self.assertTrue(len(result) > 0)
        history = CacheRepository.get_history(CS_KEY.format(user_id=self.user_id))
        assert history is not None
        self.assertIsNotNone(history)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "질문입니다.")
