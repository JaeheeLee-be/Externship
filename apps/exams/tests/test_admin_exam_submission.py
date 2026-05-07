from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.test import APIClient, APITestCase
from django.urls import reverse

from apps.exams.models import Exam, ExamDeployment, ExamSubmission
from apps.posts.models import Cohort, Course, Subject
from apps.users.models import User


class BaseTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@test.com",
            password="test1234!",
            name="테스터",
            nickname="tester",
            phone_number="010-1234-5678",
            is_active=True,
            role="STUDENT",
        )
        cls.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="test1234!",
            name="관리자",
            nickname="admin",
            phone_number="010-2222-5678",
            is_active=True,
            role="ADMIN",
        )

        cls.course = Course.objects.create(name="웹 개발", tag="WEB")
        cls.subject = Subject.objects.create(
            course=cls.course,
            title="html",
            number_of_days=30,
            number_of_hours=60,
        )
        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date="2024-01-01",
            end_date="2024-12-31",
        )

        cls.exam1 = Exam.objects.create(subject=cls.subject, title="시험1")
        cls.exam2 = Exam.objects.create(subject=cls.subject, title="시험2")

        cls.deployment1 = ExamDeployment.objects.create(
            exam=cls.exam1,
            cohort=cls.cohort,
            access_code="access-code-1",
            open_at="2024-01-01T00:00:00Z",
            close_at="2024-12-31T23:59:59Z",
        )
        cls.deployment2 = ExamDeployment.objects.create(
            exam=cls.exam2,
            cohort=cls.cohort,
            access_code="access-code-2",
            open_at="2024-01-01T00:00:00Z",
            close_at="2024-12-31T23:59:59Z",
        )

        cls.submission1 = ExamSubmission.objects.create(
            submitter=cls.user,
            deployment=cls.deployment1,
            started_at=timezone.now(),
            score=80,
            correct_answer_count=8,
        )
        cls.submission2 = ExamSubmission.objects.create(
            submitter=cls.admin,
            deployment=cls.deployment2,
            started_at=timezone.now(),
            score=90,
            correct_answer_count=9,
        )


class TestExamSubmissionAPI(BaseTestCase):
    def setUp(self):
        self.client = APIClient()

    # 권한
    def test_submission_get_as_admin(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam-deployment"))

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["submission_id"], 1)
        self.assertEqual(response.data["results"][0]["score"], 90)
        self.assertEqual(response.data["count"],2)

    def test_submission_get_as_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("exam-deployment"))

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "쪽지시험 응시 내역 조회 권한이 없습니다.")

    def test_submission_get_no_authenticate(self):
        response = self.client.get(reverse("exam-deployment"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")


    def asdjfahk(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam-deployment"), {"sort": "created_at", "order": "asc"})

        self.assertEqual(response.data["results"][0]["score"], 80)