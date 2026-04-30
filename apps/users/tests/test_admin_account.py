from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User


def create_user(
    email: str,
    nickname: str,
    role: str = "USER",
    is_active: bool = True,
) -> User:
    unique_suffix = str(abs(hash(email)))[:8]
    return User.objects.create_user(
        email=email,
        password="Test1234!",
        nickname=nickname,
        name="Tester",
        phone_number=f"010{unique_suffix}",
        role=role,
        is_active=is_active,
    )


class AdminAccountListViewTest(APITestCase):
    admin: User
    user: User
    inactive: User
    student: User

    @classmethod
    def setUpTestData(cls) -> None:
        User.objects.all().delete()
        cls.admin = create_user("admin@test.com", "admin_nick", role="ADMIN")
        cls.user = create_user("user@test.com", "user_nick", role="USER", is_active=True)
        cls.inactive = create_user("inactive@test.com", "inact_nick", role="USER", is_active=False)
        cls.student = create_user("student@test.com", "student_nk", role="STUDENT", is_active=True)

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("users:admin-account-list")

    # ── 인증 / 권한 ───────────────────────────────────────────────────────────

    def test_unauthenticated_returns_401(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_role_returns_403(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_returns_200(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── 응답 구조 ─────────────────────────────────────────────────────────────

    def test_response_has_required_keys(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)

    def test_result_item_has_expected_fields(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        expected_fields = {"id", "email", "nickname", "name", "birthday", "is_active", "role", "created_at"}
        self.assertEqual(set(response.data["results"][0].keys()), expected_fields)

    # ── 검색 ──────────────────────────────────────────────────────────────────

    def test_search_by_email(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"search": "user@test.com"})
        emails = [r["email"] for r in response.data["results"]]
        self.assertIn("user@test.com", emails)

    # ── 필터 ──────────────────────────────────────────────────────────────────

    def test_filter_is_active_true(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_active": "true"})
        self.assertTrue(all(r["is_active"] for r in response.data["results"]))

    def test_filter_is_active_false(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_active": "false"})
        self.assertTrue(all(not r["is_active"] for r in response.data["results"]))

    def test_filter_role_student(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"role": "STUDENT"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], "student@test.com")

    # ── 페이지네이션 ──────────────────────────────────────────────────────────

    def test_pagination_next_url_exists(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 1, "page_size": 2})
        self.assertIsNotNone(response.data["next"])
        self.assertIn("page=2", response.data["next"])

    def test_pagination_no_previous_on_first_page(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 1, "page_size": 10})
        self.assertIsNone(response.data["previous"])

    # ── 유효성 검사 ───────────────────────────────────────────────────────────

    def test_invalid_role_param_returns_400(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"role": "SUPERUSER"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_page_param_returns_400(self) -> None:
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
