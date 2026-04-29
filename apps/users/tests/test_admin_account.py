from __future__ import annotations

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


URL = "/api/v1/admin/accounts"


def make_user(**kwargs) -> User:
    defaults = {
        "email": "user@test.com",
        "nickname": "닉네임",
        "name": "이름",
        "role": "user",
        "status": "active",
    }
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_unusable_password()
    user.save()
    return user


# ── 인증 / 권한 ────────────────────────────────────────────────────────────────


class AdminAccountAuthTest(APITestCase):
    def test_no_token_returns_401_with_error_detail(self) -> None:
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_non_admin_returns_403_with_error_detail(self) -> None:
        user = make_user(email="staff@test.com", role="staff")
        self.client.force_authenticate(user=user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)


# ── 정상 조회 ──────────────────────────────────────────────────────────────────


class AdminAccountListTest(APITestCase):
    admin: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(email="admin@test.com", role="admin")
        make_user(email="user1@test.com", nickname="유저1", role="user", status="active")
        make_user(email="user2@test.com", nickname="유저2", role="staff", status="inactive")
        make_user(email="user3@test.com", nickname="유저3", role="student", status="withdrew")

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.admin)

    def test_returns_200_with_response_structure(self) -> None:
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["count", "next", "previous", "results"]:
            self.assertIn(key, response.data)
        self.assertEqual(response.data["count"], User.objects.count())

    def test_results_contain_required_fields(self) -> None:
        response = self.client.get(URL)
        result = response.data["results"][0]

        for field in ["id", "email", "nickname", "name", "birthday", "status", "role", "created_at"]:
            self.assertIn(field, result)


# ── 필터링 ─────────────────────────────────────────────────────────────────────


class AdminAccountFilterTest(APITestCase):
    admin: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(email="admin@test.com", role="admin")
        make_user(email="search_target@test.com", nickname="검색대상", role="user", status="active")
        make_user(email="other@test.com", nickname="다른유저", role="staff", status="inactive")
        make_user(email="student@test.com", nickname="학생", role="student", status="withdrew")

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.admin)

    def test_search_by_email_or_nickname(self) -> None:
        response_email = self.client.get(URL, {"search": "search_target"})
        response_nickname = self.client.get(URL, {"search": "검색대상"})

        self.assertEqual(response_email.data["count"], 1)
        self.assertEqual(response_nickname.data["count"], 1)

    def test_filter_by_status(self) -> None:
        response = self.client.get(URL, {"status": "inactive"})

        self.assertTrue(all(r["status"] == "inactive" for r in response.data["results"]))

    def test_filter_by_role(self) -> None:
        response = self.client.get(URL, {"role": "student"})

        self.assertTrue(all(r["role"] == "student" for r in response.data["results"]))

    def test_invalid_query_param_returns_400(self) -> None:
        response_status = self.client.get(URL, {"status": "invalid"})
        response_role = self.client.get(URL, {"role": "invalid"})

        self.assertEqual(response_status.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_role.status_code, status.HTTP_400_BAD_REQUEST)


# ── 페이지네이션 ───────────────────────────────────────────────────────────────


class AdminAccountPaginationTest(APITestCase):
    admin: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = make_user(email="admin@test.com", role="admin")
        for i in range(1, 16):  # 15명 생성
            make_user(email=f"user{i}@test.com", nickname=f"유저{i}")

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.admin)

    def test_page_size_and_next_url(self) -> None:
        response = self.client.get(URL, {"page": 1, "page_size": 5})

        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_previous_url_on_second_page(self) -> None:
        response = self.client.get(URL, {"page": 2, "page_size": 5})

        self.assertIsNotNone(response.data["previous"])

    def test_next_is_none_on_last_page(self) -> None:
        total = User.objects.count()
        response = self.client.get(URL, {"page_size": total})

        self.assertIsNone(response.data["next"])
