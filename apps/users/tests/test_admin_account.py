from __future__ import annotations

import uuid
from typing import Any

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.services.admin_account_service import AdminAccountService

URL = "/api/v1/admin/accounts"


def make_user(**kwargs: Any) -> User:
    """
    테스트용 유저 생성 헬퍼.
    - uuid 기반으로 고유값 생성 → 병렬 실행(--parallel) 환경에서도 충돌 없음
    - itertools.count 제거: 워커마다 카운터가 1부터 재시작되어 unique 충돌 발생하던 문제 해결
    """
    uid = uuid.uuid4().hex  # 32자리 hex 문자열
    defaults: dict[str, Any] = {
        "email": f"user_{uid}@test.com",
        "nickname": f"닉네임_{uid[:6]}",
        "name": "테스트이름",
        "phone_number": f"010{uid[:8]}",  # phone_number가 숫자 전용이면 아래 주석 참고
        "role": "USER",
        "is_active": True,
    }
    # phone_number 컬럼이 숫자만 허용할 경우 아래로 교체:
    # import random
    # "phone_number": f"010{random.randint(10_000_000, 99_999_999)}",
    defaults.update(kwargs)
    user = User(**defaults)
    user.set_unusable_password()
    user.save()
    return user


# ── 인증 / 권한 ────────────────────────────────────────────────────────────────


class AdminAccountAuthTest(APITestCase):
    """인증·권한 관련 테스트"""

    def test_no_token_returns_401(self) -> None:
        """토큰 없이 요청하면 401"""
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_non_admin_returns_403(self) -> None:
        """role이 ADMIN이 아닌 유저는 403"""
        user = make_user(role="USER")
        self.client.force_authenticate(user=user)

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)


# ── 서비스 단위 테스트 (HTTP 없이 직접 호출) ────────────────────────────────────


class AdminAccountServiceUnitTest(APITestCase):
    """AdminAccountService를 HTTP 없이 직접 호출하는 단위 테스트"""

    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        self.active_user = make_user(role="USER", is_active=True)
        self.inactive_user = make_user(role="USER", is_active=False)
        self.student = make_user(role="STUDENT")

    def test_service_returns_all_users(self) -> None:
        """파라미터 없으면 전체 유저 수 반환"""
        result = AdminAccountService.get_account_list({"page": 1, "page_size": 10})

        self.assertEqual(result["count"], User.objects.count())

    def test_service_search_by_email(self) -> None:
        """이메일 검색 필터"""
        result = AdminAccountService.get_account_list({"search": self.active_user.email})

        self.assertEqual(result["count"], 1)

    def test_service_is_active_false_filter(self) -> None:
        """is_active=False 필터"""
        result = AdminAccountService.get_account_list({"is_active": False})

        self.assertEqual(result["count"], 1)

    def test_service_role_filter(self) -> None:
        """role=STUDENT 필터"""
        result = AdminAccountService.get_account_list({"role": "STUDENT"})

        self.assertEqual(result["count"], 1)


# ── 정상 조회 ──────────────────────────────────────────────────────────────────


class AdminAccountListTest(APITestCase):
    """회원 목록 정상 조회 테스트"""

    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        make_user(role="USER", is_active=True)
        make_user(role="USER", is_active=False)
        make_user(role="STUDENT")
        self.client.force_authenticate(user=self.admin)

    def test_returns_200_with_response_structure(self) -> None:
        """200 응답 + count/next/previous/results 키 존재 확인"""
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["count", "next", "previous", "results"]:
            self.assertIn(key, response.data)
        # API가 반환하는 count == DB의 전체 유저 수
        self.assertEqual(response.data["count"], User.objects.count())

    def test_results_contain_required_fields(self) -> None:
        """결과 항목에 필수 필드 모두 포함"""
        response = self.client.get(URL)

        self.assertGreater(len(response.data["results"]), 0)
        result = response.data["results"][0]
        for field in ["id", "email", "nickname", "name", "birthday", "is_active", "role", "created_at"]:
            self.assertIn(field, result)


# ── 필터링 ─────────────────────────────────────────────────────────────────────


class AdminAccountFilterTest(APITestCase):
    """검색·필터 테스트"""

    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")

        # 검색 전용 유저: 고정 문자열로 생성 → next(_counter) 이중 호출 문제 제거
        uid = uuid.uuid4().hex[:8]
        self.search_email = f"findme_{uid}@test.com"
        self.search_nickname = f"검색전용_{uid}"
        self.search_target = make_user(
            email=self.search_email,
            nickname=self.search_nickname,
            role="USER",
            is_active=True,
        )

        self.inactive_user = make_user(role="USER", is_active=False)
        self.student = make_user(role="STUDENT")
        self.client.force_authenticate(user=self.admin)

    def test_search_by_email(self) -> None:
        """이메일로 검색하면 해당 유저만 반환"""
        response = self.client.get(URL, {"search": "findme_"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["email"], self.search_email)

    def test_search_by_nickname(self) -> None:
        """닉네임으로 검색하면 해당 유저만 반환"""
        response = self.client.get(URL, {"search": "검색전용_"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["nickname"], self.search_nickname)

    def test_filter_by_is_active_false(self) -> None:
        """is_active=false 필터 → 비활성 유저만 반환"""
        response = self.client.get(URL, {"is_active": "false"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["count"], 0)
        self.assertTrue(all(r["is_active"] is False for r in response.data["results"]))

    def test_filter_by_role_student(self) -> None:
        """role=STUDENT 필터 → STUDENT만 반환"""
        response = self.client.get(URL, {"role": "STUDENT"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["count"], 0)
        self.assertTrue(all(r["role"] == "STUDENT" for r in response.data["results"]))

    def test_invalid_role_returns_400(self) -> None:
        """유효하지 않은 role 값은 400"""
        response = self.client.get(URL, {"role": "INVALID_ROLE"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ── 페이지네이션 ───────────────────────────────────────────────────────────────


class AdminAccountPaginationTest(APITestCase):
    """페이지네이션 테스트"""

    def setUp(self) -> None:
        self.admin = make_user(role="ADMIN")
        # 관리자 1명 + 일반 유저 15명 = 총 16명
        for _ in range(15):
            make_user()
        self.client.force_authenticate(user=self.admin)

    def test_page_size_and_next_url(self) -> None:
        """첫 페이지: results 5개, next 존재, previous 없음"""
        response = self.client.get(URL, {"page": 1, "page_size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_previous_url_on_second_page(self) -> None:
        """두 번째 페이지: previous 존재"""
        response = self.client.get(URL, {"page": 2, "page_size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["previous"])

    def test_next_is_none_on_last_page(self) -> None:
        """마지막 페이지: next 없음"""
        total = User.objects.count()
        response = self.client.get(URL, {"page": 1, "page_size": total})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["next"])

    def test_total_count_matches_db(self) -> None:
        """count 값이 DB 전체 유저 수와 일치"""
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], User.objects.count())
