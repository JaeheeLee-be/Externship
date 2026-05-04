from __future__ import annotations

import itertools
from typing import Any

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.services.admin_account_service import AdminAccountService

URL = "/api/v1/admin/accounts"

_counter = itertools.count(1)


def make_user(**kwargs: Any) -> User:
    n = next(_counter)
    defaults: dict[str, Any] = {
        "email": f"testuser{n}@test.com",
        "nickname": f"유저{n}",
        "name": "이름",
        "phone_number": f"010{n:08d}",
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
    def test_no_token_returns_401(self) -> None:
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=make_user())

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")


# ── 서비스 단위 테스트 (HTTP 없이 직접 호출) ────────────────────────────────────


class AdminAccountServiceUnitTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        self.user1 = make_user(role="USER", is_active=True)
        self.user2 = make_user(role="USER", is_active=False)
        self.student = make_user(role="STUDENT")

    def test_returns_all_users(self) -> None:
        result = AdminAccountService.get_account_list({"page": 1, "page_size": 10})

        self.assertEqual(result["count"], User.objects.count())

    def test_search_filter(self) -> None:
        result = AdminAccountService.get_account_list({"search": self.user1.email})

        self.assertEqual(result["count"], 1)

    def test_status_filter(self) -> None:
        result = AdminAccountService.get_account_list({"status": "inactive"})

        self.assertEqual(result["count"], 1)

    def test_role_filter(self) -> None:
        result = AdminAccountService.get_account_list({"role": "student"})

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
        """results 항목이 명세 필드와 정확히 일치하는지 확인"""
        response = self.client.get(URL)
        result = response.data["results"][0]

        for field in ["id", "email", "nickname", "name", "birthday", "status", "role", "created_at"]:
            self.assertIn(field, result)
        self.assertNotIn("is_active", result)


# ── 필터링 ─────────────────────────────────────────────────────────────────────


class AdminAccountFilterTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        self.search_target = make_user(email=f"findme{next(_counter)}@test.com")
        make_user(role="USER", is_active=False)
        make_user(role="STUDENT")
        self.client.force_authenticate(user=self.admin)

    def test_search_by_email(self) -> None:
        response = self.client.get(URL, {"search": "findme"})

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.search_target.email)

    def test_filter_by_status_inactive(self) -> None:
        response = self.client.get(URL, {"status": "inactive"})

        self.assertTrue(all(r["status"] == "inactive" for r in response.data["results"]))
        self.assertGreater(response.data["count"], 0)

    def test_filter_by_status_withdrew(self) -> None:
        response = self.client.get(URL, {"status": "withdrew"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(r["status"] == "withdrew" for r in response.data["results"]))

    def test_filter_by_role(self) -> None:
        response = self.client.get(URL, {"role": "student"})

        self.assertTrue(all(r["role"] == "student" for r in response.data["results"]))
        self.assertGreater(response.data["count"], 0)

    def test_invalid_role_returns_400(self) -> None:
        response = self.client.get(URL, {"role": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_status_returns_400(self) -> None:
        response = self.client.get(URL, {"status": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ── 페이지네이션 ───────────────────────────────────────────────────────────────


class AdminAccountPaginationTest(APITestCase):
    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        for _ in range(15):
            make_user()
        self.client.force_authenticate(user=self.admin)

    def test_pagination_next_and_previous(self) -> None:
        """1페이지는 next만, 2페이지는 previous도 존재하는지 확인"""
        first = self.client.get(URL, {"page": "1", "page_size": "5"})
        second = self.client.get(URL, {"page": "2", "page_size": "5"})

        self.assertEqual(len(first.data["results"]), 5)
        self.assertIsNotNone(first.data["next"])
        self.assertIsNone(first.data["previous"])
        self.assertIsNotNone(second.data["previous"])
        self.assertIn("page=2", first.data["next"])
        self.assertIn("page_size=5", first.data["next"])

    def test_next_url_preserves_query_params(self) -> None:
        """페이지 이동 시 기존 쿼리파라미터가 유지되는지 확인"""
        response = self.client.get(URL, {"page": "1", "page_size": "5", "role": "user"})

        if response.data["next"]:
            self.assertIn("role=user", response.data["next"])

    def test_next_is_none_on_last_page(self) -> None:
        total = User.objects.count()
        response = self.client.get(URL, {"page_size": str(total)})

        self.assertIsNone(response.data["next"])
