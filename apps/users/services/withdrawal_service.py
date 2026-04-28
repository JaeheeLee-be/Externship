from __future__ import annotations

from datetime import timedelta
from typing import Any, cast

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


def get_email_verify_token_cache_key(email_token: str) -> str:
    # auth_email_service.py의 verification_code()가 저장하는 토큰 캐시 키 형식
    # email_code_{email} (인증 코드, 3분) 과 구분되는 인증 완료 토큰 캐시 (10분)
    return f"email_verify_token_{email_token}"


def get_recovery_token_cache(email_token: str) -> dict[str, str]:
    # AuthPurpose에는 signup / find_password / recovery 3가지가 존재
    # purpose 검증으로 다른 목적의 토큰이 계정 복구에 사용되지 않도록 구분
    token_key = get_email_verify_token_cache_key(email_token)
    cached: Any = cache.get(token_key)

    if not isinstance(cached, dict) or cached.get("purpose") != AuthPurpose.RECOVERY.value:
        raise InvalidRecoveryTokenError()

    return cast(dict[str, str], cached)


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
    # purpose 검증 및 캐시 데이터 조회 (Serializer에서 1차 검증 후 서비스에서 이메일 추출용으로 재조회)
    cached = get_recovery_token_cache(email_token)
    email: str = cached["email"]

    # is_active=False 조건으로 탈퇴 상태 유저만 조회
    # 복구 완료 후 is_active=True가 되므로 같은 토큰 재사용 시 DoesNotExist → DeletedUserError로 자연 차단
    # cache.delete()를 별도로 호출하지 않아도 DB 상태가 재사용을 막아줌 (피드백 반영 - 중복 제거)
    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        raise DeletedUserError()

    restore_user(user)
