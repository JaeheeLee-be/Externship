from dataclasses import asdict
from unittest.mock import MagicMock, patch

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.redis_repository import CacheRepository
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.core.utils.test_factories import create_test_category_and_question
from apps.qna.chatbot.exceptions import GroqAPIError, GroqTimeoutError
from apps.qna.dtos import InitialQNA, Message
from apps.qna.exceptions import (
    ConflictException,
    ConversationOverException,
    ExternalAPIException,
    ExternalAPITimeoutException,
    GetInitialTimeoutException,
    InactiveSessionException,
    NotFoundException,
)
from apps.qna.models import Question, QuestionCategory
from apps.qna.redis.keys import INITIAL_KEY, QNA_KEY, SESSION_KEY
from apps.qna.services.chatbot_services import ChatbotService, InitialService


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

    def test_returns_full_category_path(self) -> None:
        self.assertEqual(self.category, "top > middle > bottom")

    @patch("apps.core.utils.groq_client.requests.post")
    def test_create_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService._create_initial_answer(self.question, self.category)
        self.assertEqual(result, "i am gumba")

    @patch("apps.core.utils.groq_client.requests.post")
    def test_create_initial_answer_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        with self.assertRaises(ExternalAPITimeoutException):
            InitialService._create_initial_answer(self.question, self.category)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_create_initial_answer_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        with self.assertRaises(ExternalAPIException):
            InitialService._create_initial_answer(self.question, self.category)

    @patch("apps.core.utils.groq_client.requests.post")
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

    @patch("apps.core.utils.groq_client.requests.post")
    def test_save_initial_answer_raise_409(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        with self.assertRaises(ConflictException) as e:
            InitialService.save_initial_answer(self.question.id)
        self.assertEqual(e.exception.status_code, 409)
        self.assertEqual(str(e.exception), "이미 AI가 답변을 생성했습니다.")

    @patch("apps.core.utils.groq_client.requests.post")
    def test_save_initial_answer_raise_404(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        with self.assertRaises(NotFoundException) as e:
            InitialService.save_initial_answer(9999)
        self.assertEqual(e.exception.status_code, 404)
        self.assertEqual(str(e.exception), "질문 데이터를 찾을 수 없습니다.")

    @patch("apps.core.utils.groq_client.requests.post")
    def test_save_initial_answer_save_data_equal_cached_data(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        save_data = InitialService.save_initial_answer(self.question.id)
        cached_data = CacheRepository.get_initial(f"qna_initial:{self.question.id}")
        self.assertEqual(save_data, cached_data)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_get_initial_answer_returns_cached(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        result = InitialService.get_initial_answer(self.question.id)
        self.assertEqual(result.answer, "i am gumba")

    @patch("apps.qna.services.chatbot_services.sleep")
    @patch("apps.qna.services.chatbot_services.CacheRepository.acquire_lock")
    @patch("apps.core.utils.groq_client.requests.post")
    def test_get_initial_answer_raises_timeout(
        self, mock_post: MagicMock, mock_lock: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_post.return_value = self.res
        mock_lock.return_value = False
        with self.assertRaises(GetInitialTimeoutException):
            InitialService.get_initial_answer(self.question.id)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_get_initial_answer_saves_and_returns(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService.get_initial_answer(self.question.id)
        cached = CacheRepository.get_initial(f"qna_initial:{self.question.id}")
        self.assertEqual(result, cached)


class TestChatbotService(IsolatedRedisTestClient):
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
            key=INITIAL_KEY.format(self.question_id),
            value=asdict(self.initial),
            ttl=1800,
        )

    def tearDown(self) -> None:
        super().tearDown()

    def test_response_qna_history_raises_404_when_initial_not_found(self) -> None:
        with self.assertRaises(NotFoundException):
            ChatbotService.response_qna_history(self.user_id, 9999)

    def test_response_qna_history_returns_empty_list_when_no_history(self) -> None:
        result = ChatbotService.response_qna_history(self.user_id, self.question_id)
        self.assertEqual(result, [])

    def test_response_qna_history_activates_session(self) -> None:
        ChatbotService.response_qna_history(self.user_id, self.question_id)
        session = CacheRepository.get_session(SESSION_KEY.format(self.user_id))
        self.assertEqual(session, self.question_id)

    def test_response_qna_history_returns_existing_history(self) -> None:
        history = [
            Message(role="user", content="질문입니다."),
            Message(role="assistant", content="답변입니다."),
        ]
        CacheRepository.save_history(
            key=QNA_KEY.format(self.user_id, self.question_id),
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        result = ChatbotService.response_qna_history(self.user_id, self.question_id)
        self.assertEqual(len(result), 2)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_response_qna_chat_streams_and_saves_history(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        CacheRepository.set_session(
            key=SESSION_KEY.format(self.user_id),
            value=self.question_id,
            ttl=1800,
        )
        result = list(ChatbotService.response_qna_chat(self.user_id, self.question_id, "질문입니다."))
        self.assertTrue(len(result) > 0)
        history = CacheRepository.get_history(QNA_KEY.format(self.user_id, self.question_id))
        assert history is not None
        self.assertIsNotNone(history)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[0].content, "질문입니다.")

    @patch("apps.core.utils.groq_client.requests.post")
    def test_response_qna_chat_raises_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        CacheRepository.set_session(
            key=SESSION_KEY.format(self.user_id),
            value=self.question_id,
            ttl=1800,
        )
        with self.assertRaises(ExternalAPITimeoutException):
            list(ChatbotService.response_qna_chat(self.user_id, self.question_id, "질문입니다."))

    @patch("apps.core.utils.groq_client.requests.post")
    def test_response_qna_chat_raises_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        CacheRepository.set_session(
            key=SESSION_KEY.format(self.user_id),
            value=self.question_id,
            ttl=1800,
        )
        with self.assertRaises(ExternalAPIException):
            list(ChatbotService.response_qna_chat(self.user_id, self.question_id, "질문입니다."))

    def test_validate_qna_chat_raises_403_when_session_invalid(self) -> None:
        with self.assertRaises(InactiveSessionException):
            ChatbotService.validate_qna_chat(self.user_id, self.question_id)

    def test_validate_qna_chat_raises_429_when_history_full(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(self.user_id), self.question_id, ttl=1800)
        history = [Message(role="user", content=f"{i}") for i in range(10)]
        CacheRepository.save_history(
            key=QNA_KEY.format(self.user_id, self.question_id),
            history=[asdict(m) for m in history],
            ttl=1800,
        )
        with self.assertRaises(ConversationOverException):
            ChatbotService.validate_qna_chat(self.user_id, self.question_id)

    def test_validate_qna_chat_raises_404_when_initial_not_found(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(self.user_id), self.question_id, ttl=1800)
        CacheRepository.delete(INITIAL_KEY.format(self.question_id))
        with self.assertRaises(NotFoundException):
            ChatbotService.validate_qna_chat(self.user_id, self.question_id)

    def test_validate_qna_chat_passes_when_valid(self) -> None:
        CacheRepository.set_session(SESSION_KEY.format(self.user_id), self.question_id, ttl=1800)
        ChatbotService.validate_qna_chat(self.user_id, self.question_id)
