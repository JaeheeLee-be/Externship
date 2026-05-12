from dataclasses import asdict
from unittest.mock import MagicMock, patch

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import FixedPrefixRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.qna.chatbot.exceptions import GroqTimeoutError, GroqAPIError
from apps.qna.dtos import InitialQNA, Message
from apps.qna.exceptions import NotFoundException, ExternalAPITimeoutException, ExternalAPIException, \
    InactiveSessionException, ConversationOverException
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import INITIAL_KEY, SESSION_KEY, QNA_KEY
from apps.qna.services.chatbot_qna import QNAChatbotService


class TestQNAChatbotService(FixedPrefixRedisTestClient):
    user_id: int = 1
    question_id: int = 100
    lines: list[str]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.lines = Res.make_lines()

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_iter_res(self.lines)
        self.initial = InitialQNA(
            category="test",
            title="test",
            content="test",
            answer="test",
            question_id=self.question_id,
            using_model="test",
            created_at="2024-01-01T00:00:00",
        )
        CacheRepository.save_initial(
            key=INITIAL_KEY.format(question_id=self.question_id),
            value=asdict(self.initial),
            ttl=1800,
        )

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_response_qna_history_raises_404_when_initial_not_found(self) -> None:
        with self.assertRaises(NotFoundException):
            QNAChatbotService.response_qna_history(self.user_id, 9999)

    def test_response_qna_history_returns_empty_list_when_no_history(self) -> None:
        result = QNAChatbotService.response_qna_history(self.user_id, self.question_id)
        self.assertEqual(result, [])

    def test_response_qna_history_activates_session(self) -> None:
        QNAChatbotService.response_qna_history(self.user_id, self.question_id)
        session = CacheRepository.get_session(SESSION_KEY.format(user_id=self.user_id))
        self.assertEqual(session, self.question_id)

    def test_response_qna_history_returns_existing_history(self) -> None:
        history = [
            Message(role="user", content="질문입니다."),
            Message(role="assistant", content="답변입니다."),
        ]
        CacheRepository.save_history(
            key=QNA_KEY.format(user_id=self.user_id, question_id=self.question_id),
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        result = QNAChatbotService.response_qna_history(self.user_id, self.question_id)
        self.assertEqual(len(result), 2)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_streams_and_saves_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        CacheRepository.set_session(
            key=SESSION_KEY.format(user_id=self.user_id),
            value=self.question_id,
            ttl=1800,
        )
        result = list(QNAChatbotService.response_qna_chat(self.user_id, self.question_id, "질문입니다."))
        self.assertTrue(len(result) > 0)
        history = CacheRepository.get_history(QNA_KEY.format(user_id=self.user_id, question_id=self.question_id))
        assert history is not None
        self.assertIsNotNone(history)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "질문입니다.")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_raises_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        CacheRepository.set_session(
            key=SESSION_KEY.format(user_id=self.user_id),
            value=self.question_id,
            ttl=1800,
        )
        with self.assertRaises(ExternalAPITimeoutException):
            list(QNAChatbotService.response_qna_chat(self.user_id, self.question_id, "질문입니다."))

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_raises_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        CacheRepository.set_session(
            key=SESSION_KEY.format(user_id=self.user_id),
            value=self.question_id,
            ttl=1800,
        )
        with self.assertRaises(ExternalAPIException):
            list(QNAChatbotService.response_qna_chat(self.user_id, self.question_id, "질문입니다."))

    def test_validate_qna_chat_raises_403_when_session_invalid(self) -> None:
        with self.assertRaises(InactiveSessionException):
            QNAChatbotService.validate_qna_chat(self.user_id, self.question_id)

    def test_validate_qna_chat_raises_429_when_history_full(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        history = [Message(role="user", content=f"{i}") for i in range(10)]
        CacheRepository.save_history(
            key=QNA_KEY.format(user_id=self.user_id, question_id=self.question_id),
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        with self.assertRaises(ConversationOverException):
            QNAChatbotService.validate_qna_chat(self.user_id, self.question_id)

    def test_validate_qna_chat_raises_404_when_initial_not_found(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        CacheRepository.delete(INITIAL_KEY.format(question_id=self.question_id))
        with self.assertRaises(NotFoundException):
            QNAChatbotService.validate_qna_chat(self.user_id, self.question_id)

    def test_validate_qna_chat_passes_when_valid(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        QNAChatbotService.validate_qna_chat(self.user_id, self.question_id)