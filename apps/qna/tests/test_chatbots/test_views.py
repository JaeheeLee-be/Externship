from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.urls import reverse

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.core.utils.test_factories import create_test_category_and_question
from apps.qna.dtos import InitialQNA
from apps.qna.models import Question
from apps.qna.redis import CacheRepository
from apps.qna.redis.keys import QNA_KEY, SESSION_KEY
from apps.qna.services.chatbot_services import InitialService
from apps.users.models import User


class TestInitialAiAnswerAPIView(IsolatedRedisTestClient):
    question: Question
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("ai_answer", kwargs={"question_id": cls.question.id})

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_res("i am gumba")

    def tearDown(self) -> None:
        super().tearDown()
        cache.clear()

    @patch("apps.core.utils.groq_client.requests.post")
    def test_get_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["output"], "i am gumba")
        self.assertEqual(len(response.data), 4)

    def test_get_initial_answer_unauthenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_initial_answer_not_found(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/questions/9999/ai-answer")
        self.assertEqual(response.status_code, 404)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_post_initial_answer_success(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["output"], "i am gumba")
        self.assertEqual(len(response.data), 4)

    def test_post_initial_answer_unauthenticated(self) -> None:
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_post_initial_answer_conflict(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 409)


class TestQNAChatbotAPIViewGetMethod(IsolatedRedisTestClient):
    question: Question
    user: User
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("qna_chatbot", kwargs={"question_id": cls.question.id})

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_res("i am gumba")
        self.initial = InitialQNA(
            category="top > middle > bottom",
            title="title",
            content="content",
            answer="i am gumba",
            question_id=self.question.id,
            using_model="model",
            created_at="2026-05-04",
        )
        CacheRepository.save_initial(
            key=f"qna_initial:{self.question.id}",
            value=self.initial.__dict__,
            ttl=60,
        )
        CacheRepository.set_session(SESSION_KEY.format(self.user.id), self.question.id, ttl=60)

    def test_get_unauthenticated(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_returns_200_with_history(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)

    def test_get_returns_404_when_no_initial(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/questions/9999/chatbot")
        self.assertEqual(response.status_code, 404)


class TestQNAChatbotAPIViewPostMethod(IsolatedRedisTestClient):
    question: Question
    user: User
    url: str
    lines: list[str]

    @classmethod
    def setUpTestData(cls) -> None:
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("qna_chatbot", kwargs={"question_id": cls.question.id})

        cls.lines = Res.make_lines()

    def setUp(self) -> None:
        super().setUp()
        self.res = Res.make_iter_res(self.lines)

        self.initial = InitialQNA(
            category="top > middle > bottom",
            title="title",
            content="content",
            answer="i am gumba",
            question_id=self.question.id,
            using_model="model",
            created_at="2026-05-04",
        )
        CacheRepository.save_initial(
            key=f"qna_initial:{self.question.id}",
            value=self.initial.__dict__,
            ttl=60,
        )
        CacheRepository.set_session(SESSION_KEY.format(self.user.id), self.question.id, ttl=60)

    def test_post_unauthenticated(self) -> None:
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 401)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_post_returns_streaming_response(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type"), "text/event-stream")

    def test_post_returns_400_when_message_empty(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": ""})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_message_missing(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_when_message_too_long(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "a" * 1001})
        self.assertEqual(response.status_code, 400)

    def test_post_returns_403_when_no_session(self) -> None:
        CacheRepository.delete(SESSION_KEY.format(self.user.id))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 403)

    def test_post_returns_404_when_no_initial(self) -> None:
        CacheRepository.delete(f"qna_initial:{self.question.id}")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 404)

    @patch("apps.core.utils.groq_client.requests.post")
    def test_post_returns_429_when_history_full(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        CacheRepository.save_history(
            key=QNA_KEY.format(self.user.id, self.question.id),
            history=[{"role": "user", "content": f"msg{i}"} for i in range(10)],
            ttl=60,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"message": "hello"})
        self.assertEqual(response.status_code, 429)
