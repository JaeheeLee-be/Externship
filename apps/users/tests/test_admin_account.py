from __future__ import annotations

from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


def create_user(
    email: str,
    nickname: str,
    phone_number: str,
    role: str = User.Role.USER,
    is_active: bool = True,
) -> User:
    return User.objects.create_user(
        email=email,
        password="Test1234!@",
        name="홍길동",
        nickname=nickname,
        phone_number=phone_number,
        role=role,
        is_active=is_active,
    )


class AdminAccountListViewTest(APITestCase):
    """GET /api/v1/admin/accounts 어드민 회원 목록 조회 API 테스트"""

    url: ClassVar[str]
    admin: ClassVar[User]
    normal_user: ClassVar[User]
    student: ClassVar[User]
    inactive: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.url = reverse("admin-account-list")

        cls.admin = create_user(
            email="admin@oz.com",
            nickname="관리자",
            phone_number="01000000000",
            role=User.Role.ADMIN,
        )
        cls.normal_user = create_user(
            email="user@oz.com",
            nickname="일반유저",
            phone_number="01011111111",
            role=User.Role.USER,
        )
        cls.student = create_user(
            email="student@oz.com",
            nickname="수강생닉",
            phone_number="01033333333",
            role=User.Role.STUDENT,
        )
        cls.inactive = create_user(
            email="inactive@oz.com",
            nickname="비활성유저",
            phone_number="01044444444",
            role=User.Role.USER,
            is_active=False,
        )

    # ------------------------------------------------------------------ #
    # 인증 / 권한
    # ------------------------------------------------------------------ #

    def test_unauthenticated_returns_401(self) -> None:
        """비인증 요청 → 401"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_user_returns_403(self) -> None:
        """일반 유저(USER role) 접근 → 403"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------ #
    # 기본 응답 구조
    # ------------------------------------------------------------------ #

    def test_admin_user_returns_200_with_correct_structure(self) -> None:
        """어드민 유저 접근 → 200, count/next/previous/results 구조 확인"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, response.data)

    def test_results_contain_expected_fields(self) -> None:
        """results 항목이 명세 필드와 정확히 일치하는지 확인"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        expected_fields = {"id", "email", "nickname", "name", "birthday", "is_active", "role", "created_at"}
        self.assertEqual(set(response.data["results"][0].keys()), expected_fields)

    # ------------------------------------------------------------------ #
    # 필터
    # ------------------------------------------------------------------ #

    def test_filter_is_active_true(self) -> None:
        """is_active=true → 활성 유저만 반환"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_active": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item["is_active"] for item in response.data["results"]))

    def test_filter_is_active_false(self) -> None:
        """is_active=false → 비활성 유저만 반환"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"is_active": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(not item["is_active"] for item in response.data["results"]))

    def test_filter_role(self) -> None:
        """role=STUDENT → STUDENT 유저만 반환"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"role": "STUDENT"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item["role"] == "STUDENT" for item in response.data["results"]))

    def test_filter_invalid_role_returns_400(self) -> None:
        """유효하지 않은 role 값 → 400"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"role": "SUPERUSER"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------ #
    # 페이지네이션 / 파라미터 유효성
    # ------------------------------------------------------------------ #

    def test_page_zero_returns_400(self) -> None:
        """page=0 → 400 (min_value=1)"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_page_size_over_max_returns_400(self) -> None:
        """page_size=101 → 400 (max_value=100)"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"page_size": 101})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
