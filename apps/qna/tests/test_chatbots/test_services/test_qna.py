from dataclasses import asdict
from unittest.mock import MagicMock, patch

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import FixedPrefixRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.dtos import InitialQNA, Message, QNAChatbotContext
from apps.qna.exceptions import (
    ConversationOverException,
    ExternalAPIException,
    ExternalAPITimeoutException,
    InactiveSessionException,
    NotFoundException,
)
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import INITIAL_KEY, QNA_KEY, SESSION_KEY
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
        self.key = QNA_KEY.format(user_id=self.user_id, question_id=self.question_id)

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_response_qna_history_raises_404_when_initial_not_found(self) -> None:
        with self.assertRaises(NotFoundException):
            QNAChatbotService.response_qna_history(self.user_id, 9999)

    def test_response_qna_history_returns_initial_answer_when_no_history(self) -> None:
        result = QNAChatbotService.response_qna_history(self.user_id, self.question_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].role, "assistant")
        self.assertEqual(result[0].content, self.initial.answer)

    def test_response_qna_history_activates_session(self) -> None:
        QNAChatbotService.response_qna_history(self.user_id, self.question_id)
        session = CacheRepository.get_session(SESSION_KEY.format(user_id=self.user_id))
        self.assertEqual(session, self.question_id)

    def test_response_qna_history_prepends_initial_to_existing_history(self) -> None:
        history = [
            Message(role="user", content="질문입니다."),
            Message(role="assistant", content="답변입니다."),
        ]
        CacheRepository.save_history(
            key=self.key,
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        result = QNAChatbotService.response_qna_history(self.user_id, self.question_id)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].content, self.initial.answer)  # initial이 맨 앞
        self.assertEqual(result[1].content, "질문입니다.")

    def test_make_qna_context_raises_403_when_session_invalid(self) -> None:
        # 세션 없음
        with self.assertRaises(InactiveSessionException):
            QNAChatbotService.make_qna_context(self.user_id, self.question_id)

    def test_make_qna_context_raises_403_when_session_mismatch(self) -> None:
        # 세션은 있으나 question_id가 다름
        CacheRepository.set_session(
            key=SESSION_KEY.format(user_id=self.user_id),
            value=9999,
            ttl=1800,
        )
        with self.assertRaises(InactiveSessionException):
            QNAChatbotService.make_qna_context(self.user_id, self.question_id)

    def test_make_qna_context_raises_404_when_initial_not_found(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        CacheRepository.delete(INITIAL_KEY.format(question_id=self.question_id))
        with self.assertRaises(NotFoundException):
            QNAChatbotService.make_qna_context(self.user_id, self.question_id)

    def test_make_qna_context_raises_429_when_history_full(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        history = [Message(role="user", content=f"{i}") for i in range(10)]
        CacheRepository.save_history(
            key=self.key,
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        with self.assertRaises(ConversationOverException):
            QNAChatbotService.make_qna_context(self.user_id, self.question_id)

    def test_make_qna_context_returns_context_when_valid(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        ctx = QNAChatbotService.make_qna_context(self.user_id, self.question_id)
        self.assertIsInstance(ctx, QNAChatbotContext)
        self.assertEqual(ctx.initial.question_id, self.question_id)
        self.assertEqual(ctx.key, self.key)
        # history는 비어있을 때 None
        self.assertIsNone(ctx.history)

    def test_make_qna_context_returns_existing_history(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        history = [
            Message(role="user", content="이전 질문"),
            Message(role="assistant", content="이전 답변"),
        ]
        CacheRepository.save_history(
            key=self.key,
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        ctx = QNAChatbotService.make_qna_context(self.user_id, self.question_id)
        assert ctx.history is not None
        self.assertEqual(len(ctx.history), 2)
        self.assertEqual(ctx.history[0].content, "이전 질문")

    def test_make_qna_context_refreshes_session(self) -> None:
        """컨텍스트 생성 시 세션이 갱신되어야 함."""
        CacheRepository.set_session(SESSION_KEY.format(user_id=self.user_id), self.question_id, ttl=1800)
        QNAChatbotService.make_qna_context(self.user_id, self.question_id)
        session = CacheRepository.get_session(SESSION_KEY.format(user_id=self.user_id))
        self.assertEqual(session, self.question_id)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_streams_and_saves_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = list(
            QNAChatbotService.response_qna_chat(
                initial=self.initial,
                history=None,
                key=self.key,
                message="질문입니다.",
            )
        )
        self.assertTrue(len(result) > 0)

        history = CacheRepository.get_history(self.key)
        assert history is not None
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "질문입니다.")
        self.assertEqual(history[1].role, "assistant")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_appends_to_existing_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        existing = [
            Message(role="user", content="이전 질문"),
            Message(role="assistant", content="이전 답변"),
        ]
        list(
            QNAChatbotService.response_qna_chat(
                initial=self.initial,
                history=existing,
                key=self.key,
                message="새 질문",
            )
        )
        history = CacheRepository.get_history(self.key)
        assert history is not None
        self.assertEqual(len(history), 4)
        self.assertEqual(history[2].content, "새 질문")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_raises_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        with self.assertRaises(ExternalAPITimeoutException):
            list(
                QNAChatbotService.response_qna_chat(
                    initial=self.initial,
                    history=None,
                    key=self.key,
                    message="질문입니다.",
                )
            )

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_response_qna_chat_raises_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        with self.assertRaises(ExternalAPIException):
            list(
                QNAChatbotService.response_qna_chat(
                    initial=self.initial,
                    history=None,
                    key=self.key,
                    message="질문입니다.",
                )
            )


class TestGetQnaList(FixedPrefixRedisTestClient):

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

    def test_response_qna_list_returns_all_user_qnas(self) -> None:
        result = QNAChatbotService.response_qna_list(self.user_id)
        question_ids = {r.question_id for r in result}
        self.assertEqual(question_ids, {42, 55})

    def test_response_qna_list_last_message_is_last_item(self) -> None:
        result = QNAChatbotService.response_qna_list(self.user_id)
        for item in result:
            self.assertEqual(item.last_message, "답변입니다.")
            self.assertEqual(item.role, "assistant")

    def test_response_qna_list_returns_empty_when_no_keys(self) -> None:
        result = QNAChatbotService.response_qna_list(user_id=999)
        self.assertEqual(result, [])

    def test_response_qna_list_excludes_other_users(self) -> None:
        cache.set(f"qna_chat:999:1", self.value)
        result = QNAChatbotService.response_qna_list(self.user_id)
        question_ids = {r.question_id for r in result}
        self.assertEqual(question_ids, {42, 55})
