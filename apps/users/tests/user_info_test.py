# apps/users/tests/test_user_info_view.py
from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.posts.models.cohort import Cohort
from apps.posts.models.course import Course
from apps.users.models import CohortStudents, User


class UserInfoViewTest(APITestCase):
    user: User
    student_user: User
    course: Course
    cohort: Cohort
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("users:me")  # url name은 너 url 설정에 맞게 수정

        # 일반 유저 (수강생 등록 X)
        cls.user = User.objects.create_user(
            email="user@test.com",
            password="Test1234!",
            name="일반유저",
            nickname="일반닉",
            phone_number="01011112222",
            birthday=date(1995, 5, 10),
            gender=User.Gender.MALE,
            profile_img_url="https://example.com/profile.jpg",
        )

        # 수강생 유저 (cohort 등록됨)
        cls.student_user = User.objects.create_user(
            email="student@test.com",
            password="Test1234!",
            name="수강생",
            nickname="수강닉",
            phone_number="01033334444",
            birthday=date(2000, 1, 1),
            gender=User.Gender.FEMALE,
            role=User.Role.STUDENT,
        )

        cls.course = Course.objects.create(name="백엔드", tag="BE")
        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        CohortStudents.objects.create(user=cls.student_user, cohort=cls.cohort)

    def setUp(self) -> None:
        self.client = APIClient()

    def test_get_user_info_success(self) -> None:
        """일반 유저 정보 조회 성공 - cohort_id는 null"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["email"], "user@test.com")
        self.assertEqual(data["nickname"], "일반닉")
        self.assertEqual(data["name"], "일반유저")
        self.assertEqual(data["phone_number"], "01011112222")
        self.assertEqual(data["birthday"], "1995-05-10")
        self.assertEqual(data["gender"], "M")
        self.assertEqual(data["profile_img_url"], "https://example.com/profile.jpg")
        self.assertIsNone(data["cohort_id"])
        self.assertIn("created_at", data)

    def test_get_user_info_student_with_cohort(self) -> None:
        """수강생 유저 정보 조회 - cohort_id 포함"""
        self.client.force_authenticate(user=self.student_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["id"], self.student_user.id)
        self.assertEqual(data["email"], "student@test.com")
        self.assertEqual(data["cohort_id"], self.cohort.id)

    def test_get_user_info_unauthenticated(self) -> None:
        """비로그인 시 401"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 핸들러 적용된 응답 형태 확인 (글로벌 핸들러 적용 시)
        self.assertIn("error_detail", response.data)
        self.assertEqual(
            response.data["error_detail"],
            "자격 인증 데이터가 제공되지 않았습니다.",
        )

    def test_response_contains_only_expected_fields(self) -> None:
        """응답에 명세서에 정의된 필드만 포함되는지 확인"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        expected_fields = {
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "profile_img_url",
            "cohort_id",
            "created_at",
        }
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_password_not_in_response(self) -> None:
        """비밀번호가 응답에 노출되지 않는지 확인 (보안)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertNotIn("password", response.data)
