from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.urls import reverse
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
) -> User:
    return User.objects.create_user(
        email=email,
        password=password,
        nickname=nickname,
        name=name,
        phone_number=phone_number,
    )


def get_auth_header(user: User) -> dict[str, Any]:
    token = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {str(token.access_token)}"}


class WithdrawalViewTest(APITestCase):
    """DELETE /api/v1/accounts/me 회원 탈퇴 API 테스트"""

    def setUp(self) -> None:
        self.url = reverse("users:withdrawal")
        self.user = create_user()
        self.auth = get_auth_header(self.user)

    # ------------------------------------------------------------------ #
    # 성공 케이스
    # ------------------------------------------------------------------ #

    def test_withdraw_success(self) -> None:
        """정상 탈퇴 - 204 반환, Withdrawal 생성, is_active=False"""
        response = self.client.delete(
            self.url,
            data={"reason": "OTHER", "reason_detail": "그냥요"},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        withdrawal = Withdrawal.objects.get(user=self.user)
        self.assertEqual(withdrawal.reason, "OTHER")
        self.assertEqual(withdrawal.reason_detail, "그냥요")
        self.assertEqual(withdrawal.due_date, date.today() + timedelta(weeks=2))

    def test_withdraw_without_reason_detail(self) -> None:
        """reason_detail 없이 탈퇴 - 204 반환, reason_detail 빈 문자열로 저장"""
        response = self.client.delete(
            self.url,
            data={"reason": "GRADUATION"},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        withdrawal = Withdrawal.objects.get(user=self.user)
        self.assertEqual(withdrawal.reason_detail, "")

    # ------------------------------------------------------------------ #
    # 실패 케이스
    # ------------------------------------------------------------------ #

    def test_withdraw_unauthenticated(self) -> None:
        """비인증 요청 - 401 반환"""
        response = self.client.delete(
            self.url,
            data={"reason": "OTHER"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_withdraw_invalid_reason(self) -> None:
        """잘못된 reason 값 - 400 반환"""
        response = self.client.delete(
            self.url,
            data={"reason": "INVALID_REASON"},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdraw_missing_reason(self) -> None:
        """reason 누락 - 400 반환"""
        response = self.client.delete(
            self.url,
            data={},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_withdraw_duplicate(self) -> None:
        """이미 탈퇴 신청한 유저 재탈퇴 - 400 반환 (OneToOneField 제약)"""
        # 첫 번째 탈퇴
        self.client.delete(
            self.url,
            data={"reason": "OTHER"},
            content_type="application/json",
            **self.auth,
        )

        # is_active=False 이므로 새 토큰 발급 후 재탈퇴 시도
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        auth = get_auth_header(self.user)

        response = self.client.delete(
            self.url,
            data={"reason": "OTHER"},
            content_type="application/json",
            **auth,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteExpiredWithdrawnUsersTaskTest(APITestCase):
    """Celery 태스크 - 만료된 탈퇴 유저 영구 삭제 테스트"""

    def test_delete_expired_user(self) -> None:
        """due_date가 지난 유저는 완전 삭제됨"""
        from apps.users.tasks import delete_expired_withdrawn_users

        user = create_user(email="expired@oz.com", phone_number="01011111111")
        Withdrawal.objects.create(
            user=user,
            reason="OTHER",
            reason_detail="",
            due_date=date.today() - timedelta(days=1),  # 어제 = 만료됨
        )

        count = delete_expired_withdrawn_users()

        self.assertEqual(count, 1)
        self.assertFalse(User.objects.filter(email="expired@oz.com").exists())

    def test_not_delete_unexpired_user(self) -> None:
        """due_date가 지나지 않은 유저는 삭제되지 않음"""
        from apps.users.tasks import delete_expired_withdrawn_users

        user = create_user(email="alive@oz.com", phone_number="01022222222")
        Withdrawal.objects.create(
            user=user,
            reason="OTHER",
            reason_detail="",
            due_date=date.today() + timedelta(days=1),  # 내일 = 미만료
        )

        count = delete_expired_withdrawn_users()

        self.assertEqual(count, 0)
        self.assertTrue(User.objects.filter(email="alive@oz.com").exists())

    def test_withdrawal_record_preserved_after_user_delete(self) -> None:
        """유저 삭제 후 Withdrawal 이력은 보존됨 (SET_NULL)"""
        from apps.users.tasks import delete_expired_withdrawn_users

        user = create_user(email="history@oz.com", phone_number="01033333333")
        withdrawal = Withdrawal.objects.create(
            user=user,
            reason="GRADUATION",
            reason_detail="",
            due_date=date.today() - timedelta(days=1),
        )

        delete_expired_withdrawn_users()

        withdrawal.refresh_from_db()
        self.assertIsNone(withdrawal.user)  # user는 NULL
        self.assertEqual(withdrawal.reason, "GRADUATION")  # 이력은 보존

    def test_skip_already_null_user(self) -> None:
        """user가 이미 NULL인 Withdrawal은 건너뜀"""
        from apps.users.tasks import delete_expired_withdrawn_users

        Withdrawal.objects.create(
            user=None,
            reason="OTHER",
            reason_detail="",
            due_date=date.today() - timedelta(days=1),
        )

        count = delete_expired_withdrawn_users()

        self.assertEqual(count, 0)
