from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion
from apps.users.models import User


class AdminExamQuestionCreateViewTest(APITestCase):
    exam: Exam
    question: ExamQuestion
    client: APIClient
    admin_user: User
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_superuser(
            email="admin@test.com",
            name="admin",
            nickname="admin",
            phone_number="123456789",
            is_active=True,
            role=User.Role.ADMIN,
            password="test_password",
        )
        cls.user = User.objects.create_user(
            email="user@test.com",
            name="user",
            nickname="user",
            phone_number="01099299929",
            is_active=True,
            role=User.Role.USER,
            password="test_password",
        )
        cls.exam = Exam.objects.create(title="test_title")

    def setUp(self) -> None:
        pass

    def test_admin_create_question(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "exam": self.exam.id,
            "question": "test",
            "answer": {"answer": 1},
            "type": ExamQuestion.QuestionType.SHORT_ANSWER,
            "point": 5,
        }
        response = self.client.post(f"/api/v1/exams/admin/{self.exam.id}/questions/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExamQuestion.objects.filter(exam=self.exam).count(), 1)

    def test_user_create_question(self) -> None:
        self.client.force_authenticate(user=self.user)
        data = {"exam": self.exam.id, "question": "test", "answer": {"answer": 1}, "type": "ox", "point": 5}
        response = self.client.post(f"/api/v1/exams/admin/{self.exam.id}/questions/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_check_limit_point(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        ExamQuestion.objects.create(exam=self.exam, question="test", answer={"answer": 1}, type="ox", point=99)
        data = {"exam": self.exam.id, "question": "test_2", "answer": {"answer": 2}, "type": "ox", "point": 10}
        response = self.client.post(f"/api/v1/exams/admin/{self.exam.id}/questions/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_check_limit_question_len(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        for i in range(20):
            ExamQuestion.objects.create(
                exam=self.exam,
                question=f"test{i}",
                answer={"answer": 1},
                type=ExamQuestion.QuestionType.SHORT_ANSWER,
                point=1,
            )
        data = {
            "exam": self.exam.id,
            "question": "test_test",
            "answer": {"answer": 1},
            "type": "ox",
            "point": 5,
        }
        response = self.client.post(f"/api/v1/exams/admin/{self.exam.id}/questions/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_check_update_question(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        question = ExamQuestion.objects.create(
            exam=self.exam,
            question="test_1",
            answer={"answer": 1},
            type=ExamQuestion.QuestionType.SHORT_ANSWER,
            point=1,
        )
        data = {"exam": self.exam.id, "question": "test", "answer": {"answer": 1}, "type": "ox", "point": 5}
        response = self.client.put(f"/api/v1/exams/admin/{self.exam.id}/questions/{question.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ExamQuestion.objects.get(id=question.id).question, "test")
