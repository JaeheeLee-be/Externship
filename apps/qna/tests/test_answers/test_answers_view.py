from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


from apps.qna.models.question_models import Question, QuestionCategory

from apps.qna.models.answer_models import Answer
from apps.users.models import User


class BaseTestCase(APITestCase):
    """다른 test class 여서도 동일하게 사용가능하게 구현"""

    user: User
    category: QuestionCategory
    question: Question

    @classmethod
    def setUpTestData(cls) -> None:
        """유저 데이터 및 question test 데이터 생성"""
        cls.user = User.objects.create_user(
            name="name",
            email="test@test.com",
            nickname="test",
            phone_number="01011111111",
            gender="Male",
            birthday="2000-01-01",
            is_active=True,
            role="USER",
            password="testpassword",
        )
        cls.category = QuestionCategory.objects.create(name="python")
        cls.question = Question.objects.create(
            author=cls.user,
            category=cls.category,
            title="testquestion",
            content="testcontent",
            view_count=0,
        )


class AnswersViewTestCase(BaseTestCase):
    """
    답변 등록 API
    /api/v1/qna/questions/{question_id}/answers
    post 테스트
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_answer_create(self) -> None:
        self.answer = {
            "content": "testcontent",
            "img_urls": ["testimageurl"],
        }
        self.client.force_authenticate(user=self.user)
        url = reverse("question_answers", kwargs={"question_id": self.question.id})
        response = self.client.post(url, self.answer, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["question_id"], self.question.id)
        self.assertEqual(response.data["author_id"], self.user.id)
        self.assertIn("created_at", response.data)
        self.assertIn("answer_id", response.data)

    def test_answer_create_invalid(self) -> None:
        self.answer = {}
        self.client.force_authenticate(user=self.user)
        url = reverse("question_answers", kwargs={"question_id": self.question.id})
        response = self.client.post(url, self.answer, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_answer_create_question_not_found(self) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse("question_answers", kwargs={"question_id": 99999})
        response = self.client.post(url, {"content": "testcontent", "img_urls": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnswerAcceptViewTestCase(BaseTestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user2 = User.objects.create_user(
            name="name",
            email="test2@test.com",
            nickname="test2",
            phone_number="01022222222",
            gender="Male",
            birthday="2000-01-01",
            is_active=True,
            role="USER",
            password="testpassword",
        )
        self.user3 = User.objects.create_user(
            name="name",
            email="test3@test.com",
            nickname="test3",
            phone_number="01033333333",
            gender="Male",
            birthday="2000-01-01",
            is_active=True,
            role="USER",
            password="testpassword",
        )
        self.answer2 = Answer.objects.create(
            content="testcontent2",
            author=self.user2,
            question=self.question,
        )
        self.answer3 = Answer.objects.create(
            content="testcontent3",
            author=self.user3,
            question=self.question,
        )

    def test_answer_accept(self) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse("answer_accept", kwargs={"answer_id": self.answer2.id})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_adopted"])
        self.assertEqual(response.data["question_id"], self.question.id)
        self.assertEqual(response.data["answer_id"], self.answer2.id)

    def test_answer_accept_invalid(self) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse("answer_accept", kwargs={"answer_id": self.answer3.id})
        self.client.post(url, format="json")

        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_answer_accept_unauthorized(self) -> None:
        url = reverse("answer_accept", kwargs={"answer_id": self.answer2.id})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_answer_accept_question_user_not_match(self) -> None:
        self.client.force_authenticate(user=self.user2)
        url = reverse("answer_accept", kwargs={"answer_id": self.answer3.id})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_answer_accept_question_not_found(self) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse("answer_accept", kwargs={"answer_id": 99999})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
