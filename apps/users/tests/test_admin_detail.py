from __future__ import annotations

from typing import ClassVar

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawal


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


class AdminAccountDetailGetTest(APITestCase):
    """GET 회원 상세 조회 API"""

    url: ClassVar[str]
    admin: ClassVar[User]
    target: ClassVar[User]
    normal_user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = create_user("admin@oz.com", "관리자", "01000000000", role=User.Role.ADMIN)
        cls.target = create_user("user@oz.com", "일반유저", "01011111111")
        cls.normal_user = create_user("other@oz.com", "다른유저", "01022222222")

    def _url(self, pk: int) -> str:
        return reverse("admin-account-detail", kwargs={"account_id": pk})

    # ── 인증 / 권한 ──────────────────────────────────────────
    def test_unauthenticated_returns_401(self) -> None:
        res = self.client.get(self._url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_401_error_message(self) -> None:
        """401 응답 본문에 한국어 에러 메세지가 정상 출력되는지 확인"""
        res = self.client.get(self._url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        res = self.client.get(self._url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── 404 ──────────────────────────────────────────────────
    def test_not_found_returns_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self._url(99999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", res.data)
        self.assertIsInstance(res.data["error_detail"], str)

    # ── 응답 구조 (200) ───────────────────────────────────────
    def test_returns_200_with_exact_fields(self) -> None:
        """명세 필드 정확히 일치"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self._url(self.target.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        expected = {
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "role",
            "profile_img_url",
            "assigned_courses",
            "created_at",
        }
        self.assertEqual(set(res.data.keys()), expected)

    def test_assigned_courses_is_list(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self._url(self.target.pk))
        self.assertIsInstance(res.data["assigned_courses"], list)

    # ── status 필드 ───────────────────────────────────────────
    def test_status_active(self) -> None:
        """is_active=True + withdrawal 없음 → 'active'"""
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self._url(self.target.pk))
        self.assertEqual(res.data["status"], "active")

    def test_status_inactive(self) -> None:
        """is_active=False + withdrawal 없음 → 'inactive'"""
        inactive = create_user("inactive@oz.com", "비활성", "01033333333", is_active=False)
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self._url(inactive.pk))
        self.assertEqual(res.data["status"], "inactive")

    def test_status_withdrew(self) -> None:
        """Withdrawal 레코드 존재 → 'withdrew'"""
        from datetime import date, timedelta

        withdrew = create_user("withdrew@oz.com", "탈퇴유저", "01044444444")
        Withdrawal.objects.create(
            user=withdrew,
            reason=Withdrawal.Reason.GRADUATION,
            due_date=date.today() + timedelta(days=30),
        )
        self.client.force_authenticate(user=self.admin)
        res = self.client.get(self._url(withdrew.pk))
        self.assertEqual(res.data["status"], "withdrew")
