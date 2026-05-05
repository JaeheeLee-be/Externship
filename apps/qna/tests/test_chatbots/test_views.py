from unittest.mock import patch

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.core.utils.test_factories import MockedAIResponse as Res, create_test_category_and_question
from apps.qna.services.chatbot_services import InitialService
from django.urls import reverse

class TestInitialAiAnswerAPIView(IsolatedRedisTestClient):

    @classmethod
    def setUpTestData(cls):
        _, _, _, cls.question = create_test_category_and_question("gumba")
        cls.user = cls.question.author
        cls.url = reverse("ai_answer", kwargs={"question_id": cls.question.id})


    def setUp(self):
        super().setUp()
        self.res = Res.make_res("i am gumba")

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_get_initial_answer_success(self, mock):
        mock.return_value = self.res
        InitialService.save_initial_answer(self.question.id)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["output"], "i am gumba")
        self.assertEqual(len(response.data), 4)

    def test_get_initial_answer_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_initial_answer_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/questions/9999/ai-answer")
        self.assertEqual(response.status_code, 404)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_post_initial_answer_success(self, mock):
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["output"], "i am gumba")
        self.assertEqual(len(response.data), 4)

    def test_post_initial_answer_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    @patch("apps.qna.chatbot.clients.groq.requests.post")
    def test_post_initial_answer_conflict(self, mock):
        mock.return_value = self.res
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 409)