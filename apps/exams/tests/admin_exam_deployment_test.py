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


class DeploymentBaseTestCase(TestCase):
    admin_user: User
    student_user: User
    general_user: User
    course: Course
    cohort1: Cohort
    cohort2: Cohort
    subject1: Subject
    subject2: Subject
    exam1: Exam
    exam2: Exam
    exam_no_questions: Exam
    deployment1: ExamDeployment
    deployment2: ExamDeployment

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="pw1234!",
            name="관리자",
            nickname="admin",
            phone_number="01000000001",
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
        cls.cohort1 = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date="2026-01-01",
            end_date="2026-06-30",
        )
        cls.cohort2 = Cohort.objects.create(
            course=cls.course,
            number=2,
            max_student=30,
            start_date="2026-07-01",
            end_date="2026-12-31",
        )
        cls.subject1 = Subject.objects.create(
            course=cls.course, title="Python", number_of_days=30, number_of_hours=120
        )
        cls.subject2 = Subject.objects.create(
            course=cls.course, title="Django", number_of_days=20, number_of_hours=80
        )
        cls.exam1 = Exam.objects.create(subject=cls.subject1, title="Python 시험")
        cls.exam2 = Exam.objects.create(subject=cls.subject2, title="Django 시험")
        cls.exam_no_questions = Exam.objects.create(subject=cls.subject1, title="문제 없음")

        ExamQuestion.objects.create(
            exam=cls.exam1,
            question="Python 문제",
            type=ExamQuestion.QuestionType.SINGLE_CHOICE,
            answer={"answer": "1"},
            point=1,
        )
        ExamQuestion.objects.create(
            exam=cls.exam2,
            question="Django 문제",
            type=ExamQuestion.QuestionType.SINGLE_CHOICE,
            answer={"answer": "1"},
            point=1,
        )

        cls.deployment1 = ExamDeployment.objects.create(
            exam=cls.exam1,
            cohort=cls.cohort1,
            duration_time=60,
            open_at="2026-05-01T09:00:00Z",
            close_at="2026-05-01T11:00:00Z",
            questions_snapshot_json=[{"question": "Python 문제"}],
            access_code="code0001",
        )
        cls.deployment2 = ExamDeployment.objects.create(
            exam=cls.exam2,
            cohort=cls.cohort2,
            duration_time=60,
            open_at="2026-06-01T09:00:00Z",
            close_at="2026-06-01T11:00:00Z",
            questions_snapshot_json=[{"question": "Django 문제"}],
            access_code="code0002",
        )

    def setUp(self) -> None:
        self.client = APIClient()


class AdminExamDeploymentCreateViewTest(DeploymentBaseTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.url = reverse("exam-deployment")
        cls.valid_data = {
            "exam_id": cls.exam1.id,
            "cohort_id": cls.cohort2.id,
            "duration_time": 60,
            "open_at": "2026-07-01T09:00:00Z",
            "close_at": "2026-07-01T11:00:00Z",
        }

    # =====================
    # 권한 케이스
    # =====================

    def test_admin_can_create_deployment(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_user_cannot_create_deployment(self) -> None:
        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_student_user_cannot_create_deployment(self) -> None:
        self.client.force_authenticate(user=self.student_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "쪽지시험 배포 생성 권한이 없습니다.")

    # =====================
    # 기능 성공 케이스
    # =====================

    def test_create_deployment_success(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # =====================
    # 기능 실패 케이스
    # =====================

    def test_create_deployment_fail_400_when_open_at_is_later_than_close_at(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {**self.valid_data, "open_at": "2026-07-01T11:00:00Z", "close_at": "2026-07-01T09:00:00Z"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않은 배포 생성 요청입니다.")

    def test_create_deployment_fail_400_when_open_at_equals_close_at(self) -> None:
        self.client.force_authenticate(user=self.admin_user)
        data = {**self.valid_data, "open_at": "2026-07-01T09:00:00Z", "close_at": "2026-07-01T09:00:00Z"}

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


class AdminExamDeploymentListViewTest(DeploymentBaseTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.url = reverse("exam-deployment-list")

    # =====================
    # 권한 케이스
    # =====================

    def test_admin_can_get_deployment_list(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_get_list(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_student_user_cannot_get_list(self) -> None:
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "쪽지시험 배포 목록 조회 권한이 없습니다.")

    def test_general_user_cannot_get_list(self) -> None:
        self.client.force_authenticate(user=self.general_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "쪽지시험 배포 목록 조회 권한이 없습니다.")

    # =====================
    # 기능 성공 케이스
    # =====================

    def test_filter_by_subject_id(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"subject_id": self.subject1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_cohort_id(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"cohort_id": self.cohort1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_search_keyword(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"search_keyword": "Python"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_search_keyword_not_found(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"search_keyword": "없는시험"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sort_by_created_at_desc(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"sort": "created_at", "order": "desc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sort_by_created_at_asc(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"sort": "created_at", "order": "asc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sort_by_submit_count(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"sort": "submit_count", "order": "desc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sort_by_avg_score(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"sort": "avg_score", "order": "desc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # =====================
    # 기능 실패 케이스
    # =====================

    def test_invalid_sort_value_returns_400(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"sort": "invalid_field"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_order_value_returns_400(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"order": "invalid_order"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
