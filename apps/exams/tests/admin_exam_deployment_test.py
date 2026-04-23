from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.exams.models.exam_deployment_model import ExamDeployment
from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion


class AdminExamDeploymentCreateViewTest(TestCase):
    url: str
    exam: Exam
    exam_no_questions: Exam
    question: ExamQuestion

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("exam-deployment-create")
        cls.exam = Exam.objects.create(title="테스트 시험")
        cls.question = ExamQuestion.objects.create(
            exam=cls.exam,
            question="1 + 1은?",
            type=ExamQuestion.QuestionType.SINGLE_CHOICE,
            answer={"answer": "2"},
            point=1,
        )

        cls.exam_no_questions = Exam.objects.create(title="문제 없음")

    def setUp(self) -> None:
        self.client = APIClient()

    def test_create_deployment_fail_when_deployment_already_exists(self) -> None:
        data = {
            "exam": self.exam.id,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }
        self.client.post(self.url, data, format="json")
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_create_deployment_success(self) -> None:
        data = {
            "exam": self.exam.id,
            "cohort": 1,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "배포가 생성되었습니다.")  # type: ignore
        self.assertIn("id", response.data)  # type: ignore

    def test_create_deployment_fail_when_exam_has_no_questions(self) -> None:
        data = {
            "exam": self.exam_no_questions.id,
            "cohort": 1,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_deployment_fail_when_open_at_is_later_than_close_at(self) -> None:
        data = {
            "exam": self.exam.id,
            "cohort": 1,
            "duration_time": 60,
            "open_at": "2026-05-01T11:00:00Z",
            "close_at": "2026-05-01T09:00:00Z",
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_deployment_fail_when_required_fields_missing(self) -> None:
        data = {
            "exam": self.exam.id,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_deployment_initial_status_is_off(self) -> None:
        data = {
            "exam": self.exam.id,
            "cohort": 1,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }
        response = self.client.post(self.url, data, format="json")

        deployment = ExamDeployment.objects.get(id=response.data["id"])  # type: ignore
        self.assertEqual(deployment.status, ExamDeployment.ExamStatus.OFF)

    def test_create_deployment_access_code_is_generated(self) -> None:
        data = {
            "exam": self.exam.id,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }
        response = self.client.post(self.url, data, format="json")

        deployment = ExamDeployment.objects.get(id=response.data["id"])  # type: ignore
        self.assertIsNotNone(deployment.access_code)
        self.assertEqual(len(deployment.access_code), 8)

    def test_create_deployment_questions_snapshot_is_saved(self) -> None:
        data = {
            "exam": self.exam.id,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }
        response = self.client.post(self.url, data, format="json")

        deployment = ExamDeployment.objects.get(id=response.data["id"])  # type: ignore
        self.assertEqual(len(deployment.questions_snapshot_json), 1)
        self.assertEqual(deployment.questions_snapshot_json[0]["id"], self.question.id)
