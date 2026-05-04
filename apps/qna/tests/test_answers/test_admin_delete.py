from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.qna.models.answer_models import Answer, AnswerComment
from apps.qna.models.question_models import Question, QuestionCategory
from apps.users.models import User


class BaseTestCase(APITestCase):
    """다른 test class 여서도 동일하게 사용가능하게 구현"""

    user: User
    user2: User
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
            role="ADMIN",
            password="testpassword",
        )
        cls.user2 = User.objects.create_user(
            name="name",
            email="test2@test.com2",
            nickname="test2",
            phone_number="01022222222",
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


class AdminAnswerDeleteTestCase(BaseTestCase):
    """
    DELETE api/v1/admin/qna/answers/{answer_id}
    어드민 답변 삭제 API
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.answer = Answer.objects.create(
            content="testcontent",
            author=self.user,
            question=self.question,
        )

    def test_admin_delete_answer(self) -> None:
        """어드민 답변 삭제 답변에 댓글이 없을떄"""
        self.client.force_authenticate(user=self.user)
        url = reverse("admin-answer-delete", kwargs={"answer_id": self.answer.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Answer.objects.count(), 0)
        self.assertEqual(response.data["deleted_comment_count"], 0)
        self.assertEqual(response.data["answer_id"], self.answer.id)

    def test_admin_delete_answer_with_comments(self) -> None:
        AnswerComment.objects.create(author=self.user, answer=self.answer, content="comment1")
        AnswerComment.objects.create(author=self.user, answer=self.answer, content="comment2")
        self.client.force_authenticate(user=self.user)
        url = reverse("admin-answer-delete", kwargs={"answer_id": self.answer.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_comment_count"], 2)

    def test_admin_delete_answer_not_found(self) -> None:
        """답변을 찾을 수 없을떄"""
        self.client.force_authenticate(user=self.user)
        url = reverse("admin-answer-delete", kwargs={"answer_id": 9999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_delete_not_authenticated(self) -> None:
        """로그인 안된 유저가 요청을 보낼떄"""
        url = reverse("admin-answer-delete", kwargs={"answer_id": self.answer.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_delete_answer_forbidden(self) -> None:
        """권한이 없는 유저가 요청을 보낼떄"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("admin-answer-delete", kwargs={"answer_id": self.answer.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
