from unittest.mock import MagicMock, patch

from django.core.cache import cache

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.test_factories import create_test_category_and_question
from apps.qna.chatbot.exceptions import GroqTimeoutError, GroqAPIError
from apps.qna.exceptions import ExternalAPITimeoutException, ExternalAPIException, ConflictException, NotFoundException, \
    GetInitialTimeoutException
from apps.qna.models import QuestionCategory, Question
from apps.qna.redis import CacheRepository
from apps.qna.services.chatbot_initial_qna import InitialService
from apps.core.utils.test_factories import MockedAIResponse as Res


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

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_create_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService._create_initial_answer(self.question, self.category)
        self.assertEqual(result, "i am gumba")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_create_initial_answer_timeout(self, mock: MagicMock) -> None:
        mock.side_effect = GroqTimeoutError
        with self.assertRaises(ExternalAPITimeoutException):
            InitialService._create_initial_answer(self.question, self.category)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_create_initial_answer_api_error(self, mock: MagicMock) -> None:
        mock.side_effect = GroqAPIError
        with self.assertRaises(ExternalAPIException):
            InitialService._create_initial_answer(self.question, self.category)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
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

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_save_initial_answer_raise_409(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        with self.assertRaises(ConflictException) as e:
            InitialService.save_initial_answer(self.question.id)
        self.assertEqual(e.exception.status_code, 409)
        self.assertEqual(str(e.exception), "이미 AI가 답변을 생성했습니다.")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_save_initial_answer_raise_404(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        with self.assertRaises(NotFoundException) as e:
            InitialService.save_initial_answer(9999)
        self.assertEqual(e.exception.status_code, 404)
        self.assertEqual(str(e.exception), "질문 데이터를 찾을 수 없습니다.")

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_save_initial_answer_save_data_equal_cached_data(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        save_data = InitialService.save_initial_answer(self.question.id)
        cached_data = CacheRepository.get_initial(f"qna_initial:{self.question.id}")
        self.assertEqual(save_data, cached_data)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_get_initial_answer_returns_cached(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        result = InitialService.get_initial_answer(self.question.id)
        self.assertEqual(result.answer, "i am gumba")

    @patch("apps.qna.services.chatbot_initial_qna.sleep")
    @patch("apps.qna.services.chatbot_initial_qna.CacheRepository.acquire_lock")
    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_get_initial_answer_raises_timeout(
        self, mock_post: MagicMock, mock_lock: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_post.return_value = self.res
        mock_lock.return_value = False
        with self.assertRaises(GetInitialTimeoutException):
            InitialService.get_initial_answer(self.question.id)

    @patch("apps.qna.chatbot.groq_clients.requests.post")
    def test_get_initial_answer_saves_and_returns(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        result = InitialService.get_initial_answer(self.question.id)
        cached = CacheRepository.get_initial(f"qna_initial:{self.question.id}")
        self.assertEqual(result, cached)