from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models.cohort import Cohort  # 예시 경로
from apps.courses.models.course import Course  # 예시 경로
from apps.users.models import StudentEnrollmentRequests, User


class AdminEnrollmentListAPITestCase(APITestCase):
    admin_user: User
    normal_user: User
    course: Course
    cohort: Cohort
    enrollment_pending: StudentEnrollmentRequests
    enrollment_accepted: StudentEnrollmentRequests

    @classmethod
    def setUpTestData(cls) -> None:
        """테스트 전체에서 공통으로 사용할 데이터베이스 객체 생성"""
        now = timezone.now()

        cls.admin_user = User.objects.create_superuser(
            email="admin@coding.com",
            password="adminpassword12!",
            name="관리자",
            nickname="admin_user",
            phone_number="01000000000",
        )
        cls.normal_user = User.objects.create_user(
            email="student@coding.com",
            password="studentpassword12!",
            name="테스트",
            nickname="student",
            phone_number="01011112222",
            gender="M",
            birthday="1998-08-29",
        )

        cls.course = Course.objects.create(name="초격차 백엔드 부트캠프", tag="BE")

        cls.cohort = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date=now.date(),
            end_date=(now + timedelta(days=90)).date(),
        )

        cls.enrollment_pending = StudentEnrollmentRequests.objects.create(
            user=cls.normal_user, cohort=cls.cohort, status="pending", created_at=now
        )
        cls.enrollment_accepted = StudentEnrollmentRequests.objects.create(
            user=cls.normal_user,
            cohort=cls.cohort,
            status="accepted",
            created_at=now + timedelta(minutes=5),  # 정렬 테스트를 위해 시간차를 둡니다.
        )

    def setUp(self) -> None:
        super().setUp()
        self.url: str = "/api/v1/admin/student-enrollments"
        self.client.force_authenticate(user=self.admin_user)

    #  정상 조회

    def test_enrollment_list_success(self) -> None:
        """정상적인 어드민 요청 시 200 상태코드 및 페이징 구조 반환"""
        response = self.client.get(self.url, {"page": 1, "page_size": 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["count", "next", "previous", "results"]:
            self.assertIn(key, response.data)
        self.assertEqual(response.data["count"], 2)

    def test_enrollment_list_contains_nested_data(self) -> None:
        """results 내부에 user, cohort, course 객체와 대문자 상태값 반환 확인"""
        response = self.client.get(self.url)
        result = response.data["results"][0]

        for field in ["id", "user", "cohort", "course", "status", "created_at"]:
            self.assertIn(field, result)

        self.assertEqual(result["user"]["name"], "테스트")
        self.assertEqual(result["cohort"]["number"], 1)
        self.assertEqual(result["course"]["name"], "초격차 백엔드 부트캠프")

        # 상태값 대문자로 포맷팅
        self.assertIn(result["status"], ["PENDING", "ACCEPTED"])

    # 필터링 및 정렬

    def test_enrollment_list_filter_by_status(self) -> None:
        """상태값 쿼리 파라미터 필터링 확인 응답에 대문자 변환"""
        response = self.client.get(self.url, {"status": "pending"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], "PENDING")

    def test_enrollment_list_invalid_status_returns_400(self) -> None:
        """선택지에 없는 잘못된 상태값 요청 시 400 반환 확인"""
        response = self.client.get(self.url, {"status": "INVALID_STATUS"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enrollment_list_ordering(self) -> None:
        """sort 기준 정렬(latest) 적용 확인"""
        response = self.client.get(self.url, {"sort": "latest"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertTrue(results[0]["created_at"] >= results[1]["created_at"])

    # 인증 및 권한

    def test_no_token_returns_401(self) -> None:
        """인증 토큰이 없는 경우 401 반환 확인"""
        self.client.logout()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_returns_403(self) -> None:
        """관리자가 아닌 일반 유저 접근 시 403 반환 확인"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
