from __future__ import annotations

from datetime import timedelta

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.users.models import User, Withdrawal
from apps.users.serializers.purpose_enum import AuthPurpose
from apps.users.utils.withdrawal_exceptions import (
    AlreadyActiveError,
    AlreadyWithdrawnError,
    DeletedUserError,
    InvalidRecoveryTokenError,
    RecoveryPeriodExpiredError,
    WithdrawalRecordNotFoundError,
)


def withdraw_user(user: User, reason: str, reason_detail: str = "") -> Withdrawal:
    try:
        with transaction.atomic():
            if Withdrawal.objects.filter(user=user).exists():
                raise AlreadyWithdrawnError()
            due_date = timezone.localdate() + timedelta(weeks=2)
            withdrawal = Withdrawal.objects.create(
                user=user,
                reason=reason,
                reason_detail=reason_detail,
                due_date=due_date,
            )
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
            return withdrawal
    except IntegrityError:
        raise AlreadyWithdrawnError()


def restore_user(user: User) -> None:
    if user.is_active:
        raise AlreadyActiveError()
    withdrawal = Withdrawal.objects.filter(user=user).first()
    if withdrawal is None:
        raise WithdrawalRecordNotFoundError()
    if withdrawal.due_date <= timezone.localdate():
        raise RecoveryPeriodExpiredError()
    with transaction.atomic():
        withdrawal.delete()
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])


def restore_user_by_token(email_token: str) -> None:
    """
    이메일 인증 토큰으로 계정을 복구합니다.

    :param email_token: 이메일 인증 후 발급된 토큰 (Redis에 저장, 10분 유효)
    :raises InvalidRecoveryTokenError: 토큰이 없거나 purpose가 recovery가 아닌 경우
    :raises DeletedUserError: 해당 이메일의 탈퇴 계정이 존재하지 않는 경우
    """
    token_key = f"email_verify_token_{email_token}"
    cached = cache.get(token_key)

    if not cached or cached.get("purpose") != AuthPurpose.RECOVERY.value:
        raise InvalidRecoveryTokenError()

    email: str = cached["email"]

    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        raise DeletedUserError()

    cache.delete(token_key)  # 유저 확인 후 토큰 삭제
    restore_user(user)
