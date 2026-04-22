from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.exams.models import Exam

User = get_user_model()


class BaseExamTestCase(APITestCase):
    user: User

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
        cls.exam = Exam.objects.create(
            subject=1,
            title="test_exam",
        )


class TestExamModel(BaseExamTestCase):
    def test_exam_title_unique_exception(self):
        with self.assertRaises(IntegrityError):
            Exam.objects.create(
                subject=1,
                title="test_exam",
            )

    def test_exam_create(self):
        exam = Exam.objects.create(
            subject=2,
            title="test_exam2",
        )
        self.assertEqual(exam.title, "test_exam2")
        self.assertCountEqual(Exam.objects.all(), [self.exam, exam])
        self.assertEqual(Exam.objects.count(), 2)


class TestExamAPI(BaseExamTestCase):
    def setUp(self):
        self.client = APIClient()

    # 쪽지시험 조회: 권한
    def test_get_list_as_admin(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject"], 1)

    def test_get_list_as_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("exam:list"))

        self.assertEqual(response.status_code, 403)
        # self.assertEqual(response.data["detail"], "쪽지시험 목록 조회 권한이 없습니다.")

    def test_get_list_unauthorized(self):
        response = self.client.get(reverse("exam:list"))

        self.assertEqual(response.status_code, 401)
        # self.assertEqual(response.data["detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    # 쪽지시험 조회: 필터
    def test_get_list_with_subject(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam:list"), {"subject": 1})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject"], 1)

    def test_get_list_with_subject_not_found(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam:list"), {"subject": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    # 쪽지시험 조회: 검색
    def test_get_list_with_search_title(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"search": "exam"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject"], 1)

    def test_get_list_with_search_subject(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"search": "html"})
        # search 내용 추후 서브젝트 1번으로 적용 필요
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject"], 1)

    def test_get_list_with_search_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"search": "not_found"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    # 쪽지시험 생성: 권한
    def test_exam_create_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject": 2,
                "title": "test_exam2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "test_exam2")
        self.assertEqual(response.data["subject"], 2)
        self.assertEqual(Exam.objects.count(), 2)

    def test_exam_create_as_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject": 2,
                "title": "test_exam2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        # self.assertEqual(response.data["detail"], "쪽지시험 생성 권한이 없습니다.")

    def test_exam_create_unauthorized(self):
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject": 2,
                "title": "test_exam2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        # self.assertEqual(response.data["detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_exam_create_not_found_subject(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject": 9999999999999999,
                "title": "test_exam2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        # self.assertEqual(response.data["detail"], "해당 과목 정보를 찾을 수 없습니다.")
