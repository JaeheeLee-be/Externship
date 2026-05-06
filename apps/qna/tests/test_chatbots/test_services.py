from unittest.mock import MagicMock, patch

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.core.utils.test_factories import create_test_category_and_question
from apps.qna.chatbot import Message
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.exceptions import (
    ConflictException,
    ConversationOverException,
    ExternalAPIException,
    ExternalAPITimeoutException,
    GetInitialTimeoutException,
    NotFoundException,
    NotFoundException, ConversationOverException, InactiveSessionException,
    InactiveSessionException,
    NotFoundException,
)
from apps.qna.models import Question, QuestionCategory
from apps.qna.redis import CacheRepository
from apps.qna.redis.dtos import InitialQNA
from apps.qna.redis.keys import QNA_KEY, SESSION_KEY
from apps.qna.services.chatbot_services import InitialService, QNAChatbotService


class TestInitialService(IsolatedRedisTestClient):
    bottom: QuestionCategory
    question: Question
    category: str

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, cls.bottom, cls.question = create_test_category_and_question("gumba")
        cls.category = InitialService._get_categories(cls.bottom)

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_res("i am gumba")

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    def test_returns_full_category_path(self) -> None:
        self.assertEqual(self.category, "top > middle > bottom")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_create_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService._create_initial_answer(self.question, self.category)
        self.assertEqual(result, "i am gumba")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_create_initial_answer_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        with self.assertRaises(ExternalAPITimeoutException):
            InitialService._create_initial_answer(self.question, self.category)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_create_initial_answer_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        with self.assertRaises(ExternalAPIException):
            InitialService._create_initial_answer(self.question, self.category)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_save_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService.save_initial_answer(self.question.id)
        self.assertEqual(result.category, self.category)
        self.assertEqual(result.title, "title")
        self.assertEqual(result.content, "content")
        self.assertEqual(result.answer, "i am gumba")
        self.assertEqual(result.question_id, self.question.id)
        self.assertEqual(result.using_model, InitialService.MODEL)
        self.assertIsNotNone(result.created_at)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_save_initial_answer_raise_409(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        with self.assertRaises(ConflictException) as e:
            InitialService.save_initial_answer(self.question.id)
        self.assertEqual(e.exception.status_code, 409)
        self.assertEqual(str(e.exception), "이미 AI가 답변을 생성했습니다.")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_save_initial_answer_raise_404(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        with self.assertRaises(NotFoundException) as e:
            InitialService.save_initial_answer(9999)
        self.assertEqual(e.exception.status_code, 404)
        self.assertEqual(str(e.exception), "질문 데이터를 찾을 수 없습니다.")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_save_initial_answer_save_data_equal_cached_data(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        save_data = InitialService.save_initial_answer(self.question.id)
        cached_data = CacheRepository.get_initial(f"qna_initial:{self.question.id}")
        self.assertEqual(save_data, cached_data)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_get_initial_answer_returns_cached(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        result = InitialService.get_initial_answer(self.question.id)
        self.assertEqual(result.answer, "i am gumba")

    @patch("apps.qna.services.chatbot_services.sleep")
    @patch("apps.qna.services.chatbot_services.CacheRepository.acquire_lock")
    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_get_initial_answer_raises_timeout(
        self, mock_post: MagicMock, mock_lock: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_post.return_value = self.res
        mock_lock.return_value = False
        with self.assertRaises(GetInitialTimeoutException):
            InitialService.get_initial_answer(self.question.id)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_get_initial_answer_saves_and_returns(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService.get_initial_answer(self.question.id)
        cached = CacheRepository.get_initial(f"qna_initial:{self.question.id}")
        self.assertEqual(result, cached)


class TestQNAChatbotService(IsolatedRedisTestClient):
    bottom: QuestionCategory
    question: Question
    initial: InitialQNA

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, cls.bottom, cls.question = create_test_category_and_question("gumba")
        cls.category = InitialService._get_categories(cls.bottom)

        cls.lines = Res.make_lines()
        cls.payload = {"test": "test"}
        cls.key = "groq_api_key"

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_iter_res(self.lines)
        self.user_id = 1

        self.initial = InitialQNA(
            category=self.category,
            title="title",
            content="content",
            answer="i am gumba",
            question_id=self.question.id,
            using_model="model",
            created_at="2026-05-06",
        )
        CacheRepository.save_initial(
            key=f"qna_initial:{self.question.id}",
            value=self.initial.__dict__,
            ttl=60,
        )

    def test_response_history_raises_404_when_no_initial(self) -> None:
        with self.assertRaises(NotFoundException):
            QNAChatbotService.response_history(self.user_id, 9999)

    def test_response_history_returns_initial_answer_when_no_history(self) -> None:
        result = QNAChatbotService.response_history(self.user_id, self.question.id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].role, "assistant")
        self.assertEqual(result[0].content, "i am gumba")

    def test_response_history_includes_existing_history(self) -> None:
        CacheRepository.save_history(
            key=QNA_KEY.format(self.user_id, self.question.id),
            history=[{"role": "user", "content": "hello"}],
            ttl=60,
        )
        result = QNAChatbotService.response_history(self.user_id, self.question.id)
        self.assertEqual(len(result), 2)

    def test_response_history_makes_session(self) -> None:
        QNAChatbotService.response_history(self.user_id, self.question.id)
        session = CacheRepository.get_session(SESSION_KEY.format(self.user_id))
        self.assertEqual(session, self.question.id)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stream_chat_yields_chunks(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        chunks = list(QNAChatbotService.stream_chat(self.user_id, self.question.id, "hello"))
        self.assertTrue(len(chunks) > 0)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stream_chat_stores_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        list(QNAChatbotService.stream_chat(self.user_id, self.question.id, "hello"))
        history = CacheRepository.get_history(QNA_KEY.format(self.user_id, self.question.id))
        self.assertIsNotNone(history)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "hello")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stream_chat_raises_429_when_history_full(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        CacheRepository.save_history(
            key=QNA_KEY.format(self.user_id, self.question.id),
            history=[{"role": "user", "content": f"msg{i}"} for i in range(8)],
            ttl=60,
        )
        with self.assertRaises(ConversationOverException):
            list(QNAChatbotService.stream_chat(self.user_id, self.question.id, "hello"))

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stream_chat_raises_404_when_no_initial(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        with self.assertRaises(NotFoundException):
            list(QNAChatbotService.stream_chat(self.user_id, 9999, "hello"))

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stream_chat_raises_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        with self.assertRaises(ExternalAPITimeoutException):
            list(QNAChatbotService.stream_chat(self.user_id, self.question.id, "hello"))

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_stream_chat_raises_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        with self.assertRaises(ExternalAPIException):
            list(QNAChatbotService.stream_chat(self.user_id, self.question.id, "hello"))

    def test_ensure_active_session_raises_when_no_session(self) -> None:
        with self.assertRaises(InactiveSessionException):
            QNAChatbotService.ensure_active_session(self.user_id, self.question.id)

    def test_ensure_active_session_passes_when_session_active(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(self.user_id), self.question.id, ttl=60)
        QNAChatbotService.ensure_active_session(self.user_id, self.question.id)

    def test_ensure_active_session_raises_when_different_question(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(self.user_id), 9999, ttl=60)
        with self.assertRaises(InactiveSessionException):
            QNAChatbotService.ensure_active_session(self.user_id, self.question.id)

    def test_ensure_initial_exist_passes_when_cached(self) -> None:
        QNAChatbotService.ensure_initial_exist(self.question.id)  # 예외 없으면 통과

    def test_ensure_initial_exist_raises_404_when_not_cached(self) -> None:
        with self.assertRaises(NotFoundException):
            QNAChatbotService.ensure_initial_exist(9999)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_store_history_deletes_when_full(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        CacheRepository.save_history(
            key=QNA_KEY.format(self.user_id, self.question.id),
            history=[{"role": "user", "content": f"msg{i}"} for i in range(8)],
            ttl=60,
        )
        QNAChatbotService._store_history(
            self.user_id,
            self.question.id,
            60,
            [Message(role="user", content="over"), Message(role="assistant", content="end")],
        )
        self.assertIsNone(CacheRepository.get_history(QNA_KEY.format(self.user_id, self.question.id)))
        self.assertIsNone(CacheRepository.get_session(SESSION_KEY.format(self.user_id)))
