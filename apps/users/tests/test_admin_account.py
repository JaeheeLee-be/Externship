from __future__ import annotations

import itertools
from typing import Any
import uuid

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.services.admin_account_service import AdminAccountService

URL = "/api/v1/admin/accounts"




def make_user(**kwargs: Any) -> User:
    uid = uuid.uuid4().hex[0:8]
    defaults: dict[str, Any] = {
        "email": f"testuser{uid}@test.com",
        "nickname": f"유저{uid}",
        "name": "이름",
        "phone_number": f"010{uid[:8]}",
        "role": "USER",
        "is_active": True,
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
        user = make_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)


# ── 서비스 단위 테스트 (HTTP 없이 직접 호출) ────────────────────────────────────


class AdminAccountServiceUnitTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        self.user1 = make_user(role="USER", is_active=True)
        self.user2 = make_user(role="USER", is_active=False)
        self.student = make_user(role="STUDENT")

    def test_service_returns_all_users(self) -> None:
        result = AdminAccountService.get_account_list({"page": 1, "page_size": 10})

        self.assertEqual(result["count"], User.objects.count())

    def test_service_search_filter(self) -> None:
        result = AdminAccountService.get_account_list({"search": self.user1.email})

        self.assertEqual(result["count"], 1)

    def test_service_is_active_filter(self) -> None:
        result = AdminAccountService.get_account_list({"is_active": False})

        self.assertEqual(result["count"], 1)

    def test_service_role_filter(self) -> None:
        result = AdminAccountService.get_account_list({"role": "STUDENT"})

        self.assertEqual(result["count"], 1)


# ── 정상 조회 ──────────────────────────────────────────────────────────────────


class AdminAccountListTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        make_user(role="USER", is_active=True)
        make_user(role="USER", is_active=False)
        make_user(role="STUDENT")
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

        for field in ["id", "email", "nickname", "name", "birthday", "is_active", "role", "created_at"]:
            self.assertIn(field, result)


# ── 필터링 ─────────────────────────────────────────────────────────────────────


class AdminAccountFilterTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        self.search_target = make_user(email="findme_unique@test.com", nickname="검색전용닉네임")
        make_user(role="USER", is_active=False)
        make_user(role="STUDENT")
        self.client.force_authenticate(user=self.admin)

    def test_search_by_email(self) -> None:
        response = self.client.get(URL, {"search": "findme"})

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.search_target.email)

    def test_search_by_nickname(self) -> None:
        response = self.client.get(URL, {"search": "검색전용닉네임"})

        self.assertEqual(response.data["count"], 1)

    def test_filter_by_is_active(self) -> None:
        response = self.client.get(URL, {"is_active": "false"})

        self.assertTrue(all(r["is_active"] is False for r in response.data["results"]))
        self.assertGreater(response.data["count"], 0)

    def test_filter_by_role(self) -> None:
        response = self.client.get(URL, {"role": "STUDENT"})

        self.assertTrue(all(r["role"] == "STUDENT" for r in response.data["results"]))
        self.assertGreater(response.data["count"], 0)

    def test_invalid_role_returns_400(self) -> None:
        response = self.client.get(URL, {"role": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ── 페이지네이션 ───────────────────────────────────────────────────────────────


class AdminAccountPaginationTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        for _ in range(15):
            make_user()
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
