from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.courses.models import Cohort
from apps.posts.models.course import Course
from apps.users.models import CohortStudents, User, Withdrawal


class AdminStudentListViewTest(APITestCase):
    admin: User
    student_active: User
    student_withdrew: User
    student_deactivated: User
    course1: Course
    course2: Course
    cohort1_in_progress: Cohort
    cohort2_preparing: Cohort
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = User.objects.create_user(
            email="admin@test.com",
            password="testpass1234",
            name="관리자",
            nickname="admin",
            phone_number="01000000000",
            role="ADMIN",
        )

        cls.student_active = User.objects.create_user(
            email="student1@test.com",
            password="testpass1234",
            name="김수강",
            nickname="student1",
            phone_number="01011111111",
            birthday=date(2000, 1, 1),
            role="STUDENT",
        )
        cls.student_withdrew = User.objects.create_user(
            email="student2@test.com",
            password="testpass1234",
            name="이탈퇴",
            nickname="student2",
            phone_number="01022222222",
            role="STUDENT",
        )
        cls.student_deactivated = User.objects.create_user(
            email="student3@test.com",
            password="testpass1234",
            name="박비활성",
            nickname="student3",
            phone_number="01033333333",
            role="STUDENT",
            is_active=False,
        )

        cls.course1 = Course.objects.create(name="백엔드 부트캠프", tag="BE1")
        cls.course2 = Course.objects.create(name="프론트엔드 부트캠프", tag="FE1")

        cls.cohort1_in_progress = Cohort.objects.create(
            course=cls.course1,
            number=1,
            max_student=30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
            status="IN_PROGRESS",
        )
        cls.cohort2_preparing = Cohort.objects.create(
            course=cls.course2,
            number=1,
            max_student=30,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30),
            status="PREPARING",
        )

        CohortStudents.objects.create(user=cls.student_active, cohort=cls.cohort1_in_progress)
        CohortStudents.objects.create(user=cls.student_withdrew, cohort=cls.cohort2_preparing)

        Withdrawal.objects.create(
            user=cls.student_withdrew,
            reason="OTHER",
            due_date=date(2024, 12, 31),
        )

        cls.url = reverse("admin-students-list")

    def setUp(self) -> None:
        self.client = APIClient()

    # ===== 권한 테스트 =====

    def test_비인증_요청_401(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_일반유저_요청_403(self) -> None:
        normal_user = User.objects.create_user(
            email="user@test.com",
            password="testpass1234",
            name="일반",
            nickname="normal",
            phone_number="01099999999",
            role="USER",
        )
        self.client.force_authenticate(user=normal_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_수강생_요청_403(self) -> None:
        self.client.force_authenticate(user=self.student_active)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_관리자_요청_200(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===== 응답 구조 테스트 =====

    def test_응답_페이지네이션_구조(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_응답_필드_구조(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        first_user = response.data["results"][0]
        expected_fields = {
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "status",
            "role",
            "in_progress_course",
            "created_at",
        }
        self.assertEqual(set(first_user.keys()), expected_fields)

    # ===== status 필드 테스트 =====

    def test_status_탈퇴자는_WITHDREW(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        target = next(u for u in response.data["results"] if u["id"] == self.student_withdrew.id)
        self.assertEqual(target["status"], "WITHDREW")

    def test_status_활성유저는_ACTIVATED(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        target = next(u for u in response.data["results"] if u["id"] == self.student_active.id)
        self.assertEqual(target["status"], "ACTIVATED")

    def test_status_비활성유저는_DEACTIVATED(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        target = next(u for u in response.data["results"] if u["id"] == self.student_deactivated.id)
        self.assertEqual(target["status"], "DEACTIVATED")

    # ===== in_progress_course 필드 테스트 =====

    def test_in_progress_course_진행중기수있으면_데이터반환(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        target = next(u for u in response.data["results"] if u["id"] == self.student_active.id)
        self.assertIsNotNone(target["in_progress_course"])
        self.assertEqual(target["in_progress_course"]["cohort"]["id"], self.cohort1_in_progress.id)
        self.assertEqual(target["in_progress_course"]["course"]["id"], self.course1.id)

    def test_in_progress_course_진행중기수없으면_None(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        target = next(u for u in response.data["results"] if u["id"] == self.student_withdrew.id)
        self.assertIsNone(target["in_progress_course"])

    # ===== 검색 기능 테스트 =====

    def test_검색_이메일(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "student1@test.com"})
        ids = [u["id"] for u in response.data["results"]]
        self.assertIn(self.student_active.id, ids)
        self.assertNotIn(self.student_withdrew.id, ids)

    def test_검색_이름(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "김수강"})
        ids = [u["id"] for u in response.data["results"]]
        self.assertEqual(ids, [self.student_active.id])

    def test_검색_닉네임(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "student2"})
        ids = [u["id"] for u in response.data["results"]]
        self.assertEqual(ids, [self.student_withdrew.id])

    def test_검색_휴대폰번호(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "01033333333"})
        ids = [u["id"] for u in response.data["results"]]
        self.assertEqual(ids, [self.student_deactivated.id])

    def test_검색_결과없음(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "존재하지않는검색어"})
        self.assertEqual(response.data["count"], 0)

    # ===== 필터링 테스트 =====

    def test_필터_course_id(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"course_id": self.course1.id})
        ids = [u["id"] for u in response.data["results"]]
        self.assertIn(self.student_active.id, ids)
        self.assertNotIn(self.student_withdrew.id, ids)

    def test_필터_cohort_id(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"cohort_id": self.cohort1_in_progress.id})
        ids = [u["id"] for u in response.data["results"]]
        self.assertEqual(ids, [self.student_active.id])

    # ===== 페이지네이션 테스트 =====

    def test_페이지네이션_page_size(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page_size": 2})
        self.assertEqual(len(response.data["results"]), 2)

    def test_페이지네이션_유효하지않은_페이지_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 9999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
