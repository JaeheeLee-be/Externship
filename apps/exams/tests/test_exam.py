from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from apps.posts.models import Subject

from apps.exams.models import Exam

User = get_user_model()


class ExamBaseTestCase(APITestCase):
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
        cls.subject_html = Subject.objects.create(title="html")
        cls.subject_python = Subject.objects.create(title="python")
        cls.exam1 = Exam.objects.create(
            subject=cls.subject_html,
            title="test_exam",
        )
        cls.exam2 = Exam.objects.create(
            subject=cls.subject_python,
            title="test_exam2",
        )

# 모델 테스트
class TestExamBaseModel(ExamBaseTestCase):
    def test_exam_title_unique_exception(self):
        with self.assertRaises(IntegrityError):
            Exam.objects.create(
                subject=self.subject_html,
                title="test_exam",
            )

    def test_exam_create(self):
        exam = Exam.objects.create(
            subject=self.subject_python,
            title="new_exam",
        )
        self.assertEqual(exam.title, "new_exam")
        self.assertCountEqual(Exam.objects.all(), [self.exam1, self.exam2, exam])
        self.assertEqual(Exam.objects.count(), 3)


class TestExamBaseAPI(ExamBaseTestCase):
    def setUp(self):
        self.client = APIClient()

    # 쪽지시험 목록 조회: 권한
    def test_get_exam_list_as_admin(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam2")
        self.assertEqual(response.data["results"][0]["subject_name"], "python")

    def test_get_exam_list_as_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("exam:list"))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "쪽지시험 목록 조회 권한이 없습니다.")

    def test_get_exam_list_unauthorized(self):
        response = self.client.get(reverse("exam:list"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    # 쪽지시험 목록 조회: 필터
    def test_get_exam_list_with_subject(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam:list"), {"subject_id": 1})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    def test_get_exam_list_with_subject_not_found(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("exam:list"), {"subject_id": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    # 쪽지시험 목록 조회: 검색
    def test_get_exam_list_with_search_title(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"search_keyword": "exam"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam2")
        self.assertEqual(response.data["results"][0]["subject_name"], "python")

    def test_get_exam_list_with_search_subject(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"search_keyword": "html"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    def test_get_exam_list_with_search_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"search_keyword": "not_found"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    # 쪽지시험 목록 조회: sort
    def test_get_exam_list_with_sort(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"sort": "created_at"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    # 쪽지시험 목록 조회: order
    def test_get_exam_list_with_order(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"order": "desc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam2")
        self.assertEqual(response.data["results"][0]["subject_name"], "python")

    # 쪽지시험 목록 조회: sort + order
    def test_get_exam_list_with_sort_and_order(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("exam:list"), {"sort": "subject__title", "order": "asc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["title"], "test_exam")
        self.assertEqual(response.data["results"][0]["subject_name"], "html")

    # 쪽지시험 생성: 권한
    def test_exam_create_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "new_exam")
        self.assertEqual(response.data["subject_id"], 2)
        self.assertEqual(Exam.objects.count(), 3)

    def test_exam_create_as_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_detail"], "쪽지시험 생성 권한이 없습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    def test_exam_create_unauthorized(self):
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject_id": self.subject_python.id,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")
        self.assertEqual(Exam.objects.count(), 2)

    # 쪽지시험 생성: 없는 subject 생성
    def test_exam_create_not_found_subject(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("exam:list"),
            {
                "subject_id": 9999999999999999,
                "title": "new_exam",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error_detail"], "해당 과목 정보를 찾을 수 없습니다.")
        self.assertEqual(Exam.objects.count(), 2)

