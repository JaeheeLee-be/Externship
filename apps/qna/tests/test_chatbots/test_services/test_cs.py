from dataclasses import asdict
from unittest.mock import MagicMock, patch

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.dtos import Message
from apps.qna.exceptions import ExternalAPIException, ExternalAPITimeoutException
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import CS_KEY
from apps.qna.services.chatbot_cs import CSChatbotService


class TestCSChatbotService(IsolatedRedisTestClient):
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

    def test_response_cs_history_returns_empty_when_no_history(self) -> None:
        result = CSChatbotService.response_cs_history(self.user_id)
        self.assertEqual(result, [])

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
        self.assertEqual(result[0].role, "user")
        self.assertEqual(result[0].content, "질문입니다.")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_cs_chat_streams_and_saves_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = list(CSChatbotService.response_cs_chat(self.user_id, "질문입니다."))
        self.assertTrue(len(result) > 0)

        history = CacheRepository.get_history(CS_KEY.format(user_id=self.user_id))
        assert history is not None
        self.assertIsNotNone(history)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "질문입니다.")
        self.assertEqual(history[1].role, "assistant")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_cs_chat_appends_to_existing_history(self, mock: MagicMock) -> None:
        """이전 히스토리에 새 대화가 누적되는지 확인."""
        mock.return_value = self.res
        existing = [
            Message(role="user", content="이전 질문"),
            Message(role="assistant", content="이전 답변"),
        ]
        CacheRepository.save_history(
            key=CS_KEY.format(user_id=self.user_id),
            history=[asdict(m) for m in existing],
            ttl=1800,
        )

        list(CSChatbotService.response_cs_chat(self.user_id, "새 질문입니다."))

        history = CacheRepository.get_history(CS_KEY.format(user_id=self.user_id))
        assert history is not None
        # 이전 2건 + 새 2건 = 4건
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0].content, "이전 질문")
        self.assertEqual(history[2].role, "user")
        self.assertEqual(history[2].content, "새 질문입니다.")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_cs_chat_raises_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        with self.assertRaises(ExternalAPITimeoutException):
            list(CSChatbotService.response_cs_chat(self.user_id, "질문입니다."))

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_cs_chat_raises_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        with self.assertRaises(ExternalAPIException):
            list(CSChatbotService.response_cs_chat(self.user_id, "질문입니다."))
