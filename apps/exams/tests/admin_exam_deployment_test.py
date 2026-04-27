from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.exams.models.exam_deployment_model import ExamDeployment
from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion
from apps.posts.models.cohort import Cohort
from apps.posts.models.course import Course
from apps.posts.models.subject import Subject
from apps.users.models import User


class AdminExamDeploymentCreateViewTest(TestCase):
    url: str
    admin_user: User
    student_user: User
    general_user: User
    course: Course
    cohort: Cohort
    subject: Subject
    exam: Exam
    exam_no_questions: Exam
    question: ExamQuestion
    valid_data: dict

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("exam-deployment")

        cls.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="pw1234!",
            name="관리자",
            nickname="admin",
            phone_number="01000000001",
            role=User.Role.ADMIN,
        )
        cls.student_user = User.objects.create_user(
            email="student@example.com",
            password="pw1234!",
            name="수강생",
            nickname="student",
            phone_number="01000000002",
            role=User.Role.STUDENT,
        )
        cls.general_user = User.objects.create_user(
            email="user@example.com",
            password="pw1234!",
            name="일반유저",
            nickname="user",
            phone_number="01000000003",
            role=User.Role.USER,
        )

        cls.course = Course.objects.create(name="백엔드 부트캠프", tag="BE")
        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date="2026-01-01",
            end_date="2026-06-30",
        )
        cls.subject = Subject.objects.create(
            course=cls.course,
            title="Django",
            number_of_days=30,
            number_of_hours=120,
        )
        cls.exam = Exam.objects.create(subject=cls.subject, title="테스트 시험")
        cls.question = ExamQuestion.objects.create(
            exam=cls.exam,
            question="1 + 1은?",
            type=ExamQuestion.QuestionType.SINGLE_CHOICE,
            answer={"answer": "2"},
            point=1,
        )
        cls.exam_no_questions = Exam.objects.create(subject=cls.subject, title="문제 없음")

        cls.valid_data = {
            "exam_id": cls.exam.id,
            "cohort_id": cls.cohort.id,
            "duration_time": 60,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T11:00:00Z",
        }

    def setUp(self) -> None:
        self.client = APIClient()

    # =====================
    # 권한 성공 케이스
    # =====================

    def test_admin_can_create_deployment(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # =====================
    # 권한 실패 케이스
    # =====================

    def test_unauthenticated_user_cannot_create_deployment(self) -> None:
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_student_user_cannot_create_deployment(self) -> None:
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "쪽지시험 배포 생성 권한이 없습니다.")

    def test_general_user_cannot_create_deployment(self) -> None:
        self.client.force_authenticate(user=self.general_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "쪽지시험 배포 생성 권한이 없습니다.")

    # =====================
    # 기능 성공 케이스
    # =====================

    def test_create_deployment_returns_pk(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("pk", response.data)

    def test_create_deployment_initial_status_is_on(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        deployment = ExamDeployment.objects.get(id=response.data["pk"])
        self.assertEqual(deployment.status, ExamDeployment.ExamStatus.ON)

    def test_create_deployment_saves_question_snapshot(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        deployment = ExamDeployment.objects.get(id=response.data["pk"])
        self.assertEqual(len(deployment.questions_snapshot_json), 1)
        self.assertEqual(deployment.questions_snapshot_json[0]["question"], "1 + 1은?")

    def test_create_deployment_generates_access_code(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        deployment = ExamDeployment.objects.get(id=response.data["pk"])
        self.assertIsNotNone(deployment.access_code)
        self.assertTrue(len(deployment.access_code) > 0)

    # =====================
    # 기능 실패 케이스
    # =====================

    def test_create_deployment_fail_400_when_open_at_is_later_than_close_at(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {
            **self.valid_data,
            "open_at": "2026-05-01T11:00:00Z",
            "close_at": "2026-05-01T09:00:00Z",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 배포 생성 요청입니다.")

    def test_create_deployment_fail_400_when_open_at_equals_close_at(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {
            **self.valid_data,
            "open_at": "2026-05-01T09:00:00Z",
            "close_at": "2026-05-01T09:00:00Z",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 배포 생성 요청입니다.")

    def test_create_deployment_fail_400_when_required_fields_missing(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 배포 생성 요청입니다.")

    def test_create_deployment_fail_400_when_exam_has_no_questions(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {**self.valid_data, "exam_id": self.exam_no_questions.id}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 배포 생성 요청입니다.")

    def test_create_deployment_fail_404_when_exam_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {**self.valid_data, "exam_id": 99999}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다.")

    def test_create_deployment_fail_404_when_cohort_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {**self.valid_data, "cohort_id": 99999}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다.")

    def test_create_deployment_fail_409_when_duplicate(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        self.client.post(self.url, self.valid_data, format="json")

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error_detail"], "동일한 조건의 배포가 이미 존재합니다.")
