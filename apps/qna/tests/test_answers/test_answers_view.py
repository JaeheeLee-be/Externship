from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.answer_models import Answer
from apps.qna.models.question_models import Question, QuestionCategory
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

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user.role = "STUDENT"
        cls.user.save()

    def setUp(self) -> None:
        self.client = APIClient()

    def test_answer_create(self) -> None:
        """answer 데이터 생성 test code"""
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
        """유효하지 않은 데이터가 들어왔을때의 test code"""
        self.answer = {}
        self.client.force_authenticate(user=self.user)
        url = reverse("question_answers", kwargs={"question_id": self.question.id})
        response = self.client.post(url, self.answer, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_answer_create_question_not_found(self) -> None:
        """답변을 달 질문을 못 찾았을때의 test code"""
        self.client.force_authenticate(user=self.user)
        url = reverse("question_answers", kwargs={"question_id": 99999})
        response = self.client.post(url, {"content": "testcontent", "img_urls": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnswerAcceptViewTestCase(BaseTestCase):
    """
    POST api/v1/qna/answers/{answer_id}/accept
    답변 채택에 대한 test code
    """

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user.role = "STUDENT"
        cls.user.save()

    def setUp(self) -> None:
        """작성자와 다른 유저가 답변을 달 수 있어 더미 데이터 생성"""
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
        """채택 핸들러 test code -> 200"""
        self.client.force_authenticate(user=self.user)
        url = reverse("answer_accept", kwargs={"answer_id": self.answer2.id})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_adopted"])
        self.assertEqual(response.data["question_id"], self.question.id)
        self.assertEqual(response.data["answer_id"], self.answer2.id)

    def test_answer_accept_invalid(self) -> None:
        """답변이 이미 채택된 답변에 대한 test code -> 409"""
        self.client.force_authenticate(user=self.user)
        url = reverse("answer_accept", kwargs={"answer_id": self.answer3.id})
        self.client.post(url, format="json")

        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_answer_accept_unauthorized(self) -> None:
        """로그인 하지 않은 유저가 채택 했을떄 test code -> 401"""
        url = reverse("answer_accept", kwargs={"answer_id": self.answer2.id})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_answer_accept_question_user_not_match(self) -> None:
        """질문 작성자와 채택할 유저가 같이 않을떄 -> 403"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("answer_accept", kwargs={"answer_id": self.answer3.id})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_answer_accept_question_not_found(self) -> None:
        """채택할 답변에 대한 질문을 못 찾을떄 test code -> 404"""
        self.client.force_authenticate(user=self.user)
        url = reverse("answer_accept", kwargs={"answer_id": 99999})
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnswerUpdateTestCase(BaseTestCase):
    """
    PUT /api/v1/qna/answers/{answer_id}
    질문수정 API
    """

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user.role = "STUDENT"
        cls.user.save()

    def setUp(self) -> None:
        self.client = APIClient()

    def test_answer_update(self) -> None:
        """답변 수정 test code"""
        self.client.force_authenticate(user=self.user)
        self.answer = Answer.objects.create(
            author=self.user,
            question=self.question,
            content="testcontent",
        )
        url = reverse("answers_detail", kwargs={"answer_id": self.answer.id})
        response = self.client.put(url, {"content": "updated content", "img_urls": ["updated imageurl"]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("answer_id", response.data)
        self.assertIn("updated_at", response.data)

    def test_answer_update_unauthenticated(self) -> None:
        """로그인되지 않은 user가 put 요청을 보낼떄 test code"""
        self.answer = Answer.objects.create(
            author=self.user,
            question=self.question,
            content="testcontent",
        )
        url = reverse("answers_detail", kwargs={"answer_id": self.answer.id})
        response = self.client.put(url, {"content": "updated content", "img_urls": ["updated imageurl"]}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_answer_update_invalid(self) -> None:
        """변경할 데이터가 이상하게 들어왔을떄 test code"""
        self.client.force_authenticate(user=self.user)
        self.answer = Answer.objects.create(
            author=self.user,
            question=self.question,
            content="testcontent",
        )
        url = reverse("answers_detail", kwargs={"answer_id": self.answer.id})
        response = self.client.put(url, {"img_urls": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_answer_update_not_found(self) -> None:
        """변경할 답변을 못 찾았을떄 test code"""
        self.client.force_authenticate(user=self.user)
        url = reverse("answers_detail", kwargs={"answer_id": 10000})
        response = self.client.put(url, {"content": "updated content", "img_urls": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_answer_update_forbidden(self) -> None:
        """답변을 작성한 유저가 아닌 유저가 수정을 할떄 test code"""
        self.new_user = User.objects.create_user(
            name="test2",
            email="test2@test.com",
            nickname="test2",
            phone_number="01022222222",
            gender="Male",
            birthday="2000-01-01",
            is_active=True,
            role="USER",
            password="testpassword",
        )
        self.answer = Answer.objects.create(
            author=self.user,
            question=self.question,
            content="testcontent",
        )
        self.client.force_authenticate(user=self.new_user)
        url = reverse("answers_detail", kwargs={"answer_id": self.answer.id})
        response = self.client.put(url, {"content": "updated content", "img_urls": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
