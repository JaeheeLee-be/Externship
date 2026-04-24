from __future__ import annotations

from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawal
from apps.users.services.withdrawal_service import make_restore_token


def create_withdrawn_user(
    email: str = "withdrawn@oz.com",
    phone_number: str = "01099999999",
    due_days: int = 7,
) -> tuple[User, Withdrawal]:
    user = User.objects.create_user(
        email=email,
        password="Test1234!@",
        nickname="탈퇴자",
        name="홍길동",
        phone_number=phone_number,
    )
    user.is_active = False
    user.save(update_fields=["is_active"])
    withdrawal = Withdrawal.objects.create(
        user=user,
        reason="other",
        reason_detail="",
        due_date=date.today() + timedelta(days=due_days),
    )
    return user, withdrawal


class RestoreRequestViewTest(APITestCase):
    """POST /api/v1/accounts/recover/request 복구 요청 테스트"""

    def setUp(self) -> None:
        self.url = reverse("users:restore-request")

    def test_request_with_withdrawn_email_returns_200(self) -> None:
        """탈퇴한 이메일로 요청 시 200 반환"""
        create_withdrawn_user()
        response = self.client.post(self.url, data={"email": "withdrawn@oz.com"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_with_unknown_email_returns_200(self) -> None:
        """존재하지 않는 이메일도 200 반환 (이메일 존재 여부 노출 방지)"""
        response = self.client.post(self.url, data={"email": "nobody@oz.com"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_with_invalid_email_returns_400(self) -> None:
        """이메일 형식이 아닌 값 - 400 반환"""
        response = self.client.post(self.url, data={"email": "notanemail"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RestoreViewTest(APITestCase):
    """POST /api/v1/accounts/recover 계정 복구 테스트"""

    def setUp(self) -> None:
        self.url = reverse("users:restore")

    def test_restore_success(self) -> None:
        """유효한 토큰으로 복구 - 200 반환, is_active=True, Withdrawal 삭제"""
        user, withdrawal = create_withdrawn_user()
        token = make_restore_token(user.id)

        response = self.client.post(self.url, data={"token": token}, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(Withdrawal.objects.filter(user=user).exists())

    def test_restore_with_invalid_token_returns_400(self) -> None:
        """잘못된 토큰 - 400 반환"""
        response = self.client.post(self.url, data={"token": "invalid.token"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_with_expired_due_date_returns_400(self) -> None:
        """due_date가 지난 경우 - 400 반환"""
        user, _ = create_withdrawn_user(
            email="expired@oz.com",
            phone_number="01088888888",
            due_days=-1,
        )
        token = make_restore_token(user.id)

        response = self.client.post(self.url, data={"token": token}, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_already_deleted_user_returns_400(self) -> None:
        """유저가 이미 완전 삭제된 경우 - 400 반환"""
        user, _ = create_withdrawn_user(email="deleted@oz.com", phone_number="01077777777")
        token = make_restore_token(user.id)
        user.delete()

        response = self.client.post(self.url, data={"token": token}, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_without_token_returns_400(self) -> None:
        """토큰 누락 - 400 반환"""
        response = self.client.post(self.url, data={}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
