from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.urls import reverse

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res
from apps.core.utils.test_factories import create_test_category_and_question
from apps.qna.models import Question
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

    @patch("apps.qna.chatbot.clients.groq.requests.post")
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

    @patch("apps.qna.chatbot.clients.groq.requests.post")
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

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_post_initial_answer_conflict(self, mock: MagicMock) -> None:
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 409)
