from __future__ import annotations

from datetime import timedelta
from typing import Any, ClassVar

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User, Withdrawal


def create_user(
    email: str = "test@oz.com",
    password: str = "Test1234!@",
    nickname: str = "테스터",
    name: str = "홍길동",
    phone_number: str = "01012345678",
    role: str = User.Role.USER,
) -> User:
    return User.objects.create_user(
        email=email,
        password=password,
        nickname=nickname,
        name=name,
        phone_number=phone_number,
        role=role,
    )


def create_admin(
    email: str = "admin@oz.com",
    nickname: str = "관리자",
    phone_number: str = "01099998888",
) -> User:
    return create_user(
        email=email,
        nickname=nickname,
        phone_number=phone_number,
        role=User.Role.ADMIN,
    )


def get_auth_header(user: User) -> dict[str, Any]:
    token = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {str(token.access_token)}"}


def create_withdrawal(user: User) -> Withdrawal:
    user.is_active = False
    user.save(update_fields=["is_active"])
    return Withdrawal.objects.create(
        user=user,
        reason=Withdrawal.Reason.NO_LONGER_NEEDED,
        reason_detail="테스트 탈퇴",
        due_date=timezone.localdate() + timedelta(weeks=2),
    )


class AdminWithdrawalListViewGetTest(APITestCase):
    """GET /api/v1/admin/withdrawals 탈퇴 목록 조회"""

    url_name: ClassVar[str] = "admin-withdrawal-list"

    def setUp(self) -> None:
        self.admin = create_admin()
        self.user = create_user(
            email="student@oz.com", nickname="수강생", phone_number="01022223333", role=User.Role.STUDENT
        )
        self.other_user = create_user(email="other@oz.com", nickname="기타유저", phone_number="01033334444")
        self.withdrawal = create_withdrawal(self.user)
        self.other_withdrawal = create_withdrawal(self.other_user)
        self.auth = get_auth_header(self.admin)
        self.url = reverse(self.url_name)

    def test_admin_can_retrieve_withdrawal_list(self) -> None:
        self.assertEqual(self.url, "/api/v1/admin/withdrawals")
        response = self.client.get(self.url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertEqual(len(data["results"]), 2)
        self.assertIn("reason_display", data["results"][0])
        self.assertIn("withdrawn_at", data["results"][0])
        self.assertEqual(data["results"][0]["reason_display"], "더 이상 필요하지 않음")
        self.assertEqual(
            set(data["results"][0]["user"].keys()),
            {"id", "email", "name", "role", "birthday"},
        )

    def test_admin_can_filter_withdrawal_list_by_search_and_role(self) -> None:
        response = self.client.get(self.url, {"search": "student", "role": User.Role.STUDENT}, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["id"], self.withdrawal.id)

    def test_admin_can_control_page_size(self) -> None:
        response = self.client.get(self.url, {"page_size": 1}, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["results"]), 1)

    def test_excludes_withdrawal_without_user(self) -> None:
        Withdrawal.objects.create(
            user=None,
            reason=Withdrawal.Reason.OTHER,
            reason_detail="유저 삭제됨",
            due_date=timezone.localdate() + timedelta(weeks=2),
        )
        response = self.client.get(self.url, **self.auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 2)

    def test_returns_401_without_token(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_403_for_non_admin(self) -> None:
        normal_user = create_user(email="normal@oz.com", nickname="일반유저", phone_number="01044445555")
        auth = get_auth_header(normal_user)
        response = self.client.get(self.url, **auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
