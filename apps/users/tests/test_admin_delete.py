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


class AdminAccountDeleteTest(APITestCase):
    """DELETE 회원 삭제 API"""

    admin: ClassVar[User]
    normal_user: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = create_user("admin@oz.com", "관리자", "01000000000", role=User.Role.ADMIN)
        cls.normal_user = create_user("normal@oz.com", "일반유저", "01011111111")

    def _url(self, pk: int) -> str:
        return reverse("admin-account-delete", kwargs={"account_id": pk})

    # ── 인증 / 권한 ──────────────────────────────────────────
    def test_unauthenticated_returns_401(self) -> None:
        res = self.client.delete(self._url(self.normal_user.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_401_error_message(self) -> None:
        """401 응답 본문에 한국어 에러 메세지가 정상 출력되는지 확인"""
        res = self.client.delete(self._url(self.normal_user.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", res.data)
        self.assertEqual(res.data["error_detail"], "자격 인증 데이터가 제공되지 않았습니다.")

    def test_non_admin_returns_403(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        res = self.client.delete(self._url(self.normal_user.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # ── 404 ──────────────────────────────────────────────────
    def test_not_found_returns_404(self) -> None:
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(self._url(99999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", res.data)
        self.assertIsInstance(res.data["error_detail"], str)

    # ── 정상 삭제 (200) ───────────────────────────────────────
    def test_delete_returns_200_with_detail_message(self) -> None:
        """명세: 200 → {"detail": "유저 데이터가 삭제되었습니다. - pk: {pk}"}"""
        target = create_user("todelete@oz.com", "삭제대상", "01077777777")
        pk = target.pk
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(self._url(pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["detail"], f"유저 데이터가 삭제되었습니다. - pk: {pk}")

    def test_deleted_user_not_found_on_get(self) -> None:
        """삭제 후 동일 pk로 GET → 404"""
        target = create_user("gone@oz.com", "사라질유저", "01066666666")
        pk = target.pk
        self.client.force_authenticate(user=self.admin)
        self.client.delete(self._url(pk))
        res = self.client.get(reverse("admin-account-detail", kwargs={"account_id": pk}))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
