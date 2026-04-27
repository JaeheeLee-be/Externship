from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawal
from apps.users.services.withdrawal_service import restore_user_by_token
from apps.users.utils.withdrawal_exceptions import (
    DeletedUserError,
    InvalidRecoveryTokenError,
    RecoveryPeriodExpiredError,
)


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
        reason="OTHER",
        reason_detail="",
        due_date=date.today() + timedelta(days=due_days),
    )
    return user, withdrawal


# ------------------------------------------------------------------ #
# RestoreRequestView 테스트
# ------------------------------------------------------------------ #


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


# ------------------------------------------------------------------ #
# RestoreView 테스트 (View 레이어 - 서비스 mock)
# ------------------------------------------------------------------ #


class RestoreViewTest(APITestCase):
    """POST /api/v1/accounts/recover 계정 복구 View 테스트"""

    def setUp(self) -> None:
        self.url = reverse("users:restore")

    def test_restore_success(self) -> None:
        """유효한 email_token → 서비스 성공 → 200 반환"""
        with patch("apps.users.views.restore_view.restore_user_by_token") as mock:
            mock.return_value = None
            response = self.client.post(self.url, data={"email_token": "valid_token"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restore_invalid_token_returns_400(self) -> None:
        """서비스에서 InvalidRecoveryTokenError → 400 반환"""
        with patch("apps.users.views.restore_view.restore_user_by_token") as mock:
            mock.side_effect = InvalidRecoveryTokenError()
            response = self.client.post(self.url, data={"email_token": "bad_token"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_restore_user_not_found_returns_404(self) -> None:
        """서비스에서 DeletedUserError → 404 반환"""
        with patch("apps.users.views.restore_view.restore_user_by_token") as mock:
            mock.side_effect = DeletedUserError()
            response = self.client.post(self.url, data={"email_token": "some_token"}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_restore_without_token_returns_400(self) -> None:
        """email_token 누락 → 시리얼라이저 400 반환"""
        response = self.client.post(self.url, data={}, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------------ #
# restore_user_by_token 서비스 테스트 (캐시 mock)
# ------------------------------------------------------------------ #


class RestoreUserByTokenServiceTest(TestCase):
    """restore_user_by_token 서비스 단위 테스트"""

    def test_invalid_token_raises_error(self) -> None:
        """캐시 미스 → InvalidRecoveryTokenError"""
        with patch("apps.users.services.withdrawal_service.cache") as mock_cache:
            mock_cache.get.return_value = None
            with self.assertRaises(InvalidRecoveryTokenError):
                restore_user_by_token("invalid_token")

    def test_wrong_purpose_raises_error(self) -> None:
        """purpose가 recovery가 아닌 토큰 → InvalidRecoveryTokenError"""
        with patch("apps.users.services.withdrawal_service.cache") as mock_cache:
            mock_cache.get.return_value = {"email": "test@oz.com", "purpose": "signup"}
            with self.assertRaises(InvalidRecoveryTokenError):
                restore_user_by_token("signup_token")

    def test_deleted_user_raises_error(self) -> None:
        """DB에 유저 없음 → DeletedUserError"""
        with patch("apps.users.services.withdrawal_service.cache") as mock_cache:
            mock_cache.get.return_value = {"email": "ghost@oz.com", "purpose": "recovery"}
            with self.assertRaises(DeletedUserError):
                restore_user_by_token("ghost_token")

    def test_expired_due_date_raises_error(self) -> None:
        """복구 기간 만료 → RecoveryPeriodExpiredError"""
        user, _ = create_withdrawn_user(
            email="expired@oz.com",
            phone_number="01088888888",
            due_days=-1,
        )
        with patch("apps.users.services.withdrawal_service.cache") as mock_cache:
            mock_cache.get.return_value = {"email": user.email, "purpose": "recovery"}
            with self.assertRaises(RecoveryPeriodExpiredError):
                restore_user_by_token("expired_token")

    def test_already_active_user_raises_error(self) -> None:
        """이미 활성화된 계정 복구 시도 → DeletedUserError (is_active=False 조건 미충족)"""
        active_user = User.objects.create_user(
            email="active@oz.com",
            password="Test1234!@",
            nickname="활성유저",
            name="홍길동",
            phone_number="01055555555",
        )
        with patch("apps.users.services.withdrawal_service.cache") as mock_cache:
            mock_cache.get.return_value = {"email": active_user.email, "purpose": "recovery"}
            # is_active=True인 유저는 get(is_active=False) 에서 DoesNotExist → DeletedUserError
            with self.assertRaises(DeletedUserError):
                restore_user_by_token("active_token")

    def test_success_restores_user(self) -> None:
        """정상 복구 → is_active=True, Withdrawal 삭제"""
        user, _ = create_withdrawn_user()
        with patch("apps.users.services.withdrawal_service.cache") as mock_cache:
            mock_cache.get.return_value = {"email": user.email, "purpose": "recovery"}
            restore_user_by_token("valid_token")
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(Withdrawal.objects.filter(user=user).exists())
