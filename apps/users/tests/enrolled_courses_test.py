from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.courses.models.cohort import Cohort, StatusChoices
from apps.posts.models.course import Course
from apps.users.models import StudentEnrollmentRequests, User


class MyCoursesViewTest(APITestCase):
    user: User
    other_user: User
    course: Course
    cohort_preparing: Cohort
    cohort_in_progress: Cohort
    cohort_finished: Cohort
    cohort_pending: Cohort
    cohort_rejected: Cohort
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("users:enrolled_courses")

        cls.user = User.objects.create_user(
            email="user@test.com",
            password="Test1234!",
            name="테스트",
            nickname="테스트닉",
            phone_number="01011112222",
        )

        cls.other_user = User.objects.create_user(
            email="other@test.com",
            password="Test1234!",
            name="다른유저",
            nickname="다른닉",
            phone_number="01033334444",
        )

        cls.course = Course.objects.create(
            name="백엔드",
            tag="BE",
            thumbnail_img_url="https://example.com/thumb.png",
        )

        # 5개 cohort 생성: 다양한 status
        cls.cohort_preparing = Cohort.objects.create(
            course=cls.course,
            number=1,
            max_student=30,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            status=StatusChoices.PREPARING,
        )
        cls.cohort_in_progress = Cohort.objects.create(
            course=cls.course,
            number=2,
            max_student=30,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=StatusChoices.IN_PROGRESS,
        )
        cls.cohort_finished = Cohort.objects.create(
            course=cls.course,
            number=3,
            max_student=30,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status=StatusChoices.FINISHED,
        )
        cls.cohort_pending = Cohort.objects.create(
            course=cls.course,
            number=4,
            max_student=30,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=StatusChoices.PREPARING,
        )
        cls.cohort_rejected = Cohort.objects.create(
            course=cls.course,
            number=5,
            max_student=30,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=StatusChoices.PREPARING,
        )

        # 신청 기록:
        # 승인된 거 3개 (PREPARING, IN_PROGRESS, FINISHED) - 응답에 나와야 함
        StudentEnrollmentRequests.objects.create(
            user=cls.user,
            cohort=cls.cohort_preparing,
            status=StudentEnrollmentRequests.Status.ACCEPTED,
        )
        StudentEnrollmentRequests.objects.create(
            user=cls.user,
            cohort=cls.cohort_in_progress,
            status=StudentEnrollmentRequests.Status.ACCEPTED,
        )
        StudentEnrollmentRequests.objects.create(
            user=cls.user,
            cohort=cls.cohort_finished,
            status=StudentEnrollmentRequests.Status.ACCEPTED,
        )

        # 신청 중 (PENDING) - 응답에 안 나와야 함
        StudentEnrollmentRequests.objects.create(
            user=cls.user,
            cohort=cls.cohort_pending,
            status=StudentEnrollmentRequests.Status.PENDING,
        )

        # 거절됨 (REJECTED) - 응답에 안 나와야 함
        StudentEnrollmentRequests.objects.create(
            user=cls.user,
            cohort=cls.cohort_rejected,
            status=StudentEnrollmentRequests.Status.REJECTED,
        )

    def setUp(self) -> None:
        self.client = APIClient()

    def test_get_my_courses_success(self) -> None:
        """승인된 기수만 응답에 포함"""
        self.client.force_authenticate(user=self.user)