from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.users.models import Withdrawal
from apps.users.services.withdrawal_service import get_recovery_token_cache
from apps.users.utils.withdrawal_exceptions import InvalidRecoveryTokenError


class WithdrawalSerializer(serializers.Serializer[Any]):
    reason = serializers.ChoiceField(choices=Withdrawal.Reason.choices)
    reason_detail = serializers.CharField(required=False, default="", allow_blank=True)


class RestoreSerializer(serializers.Serializer[Any]):
    email_token = serializers.CharField()

    def validate_email_token(self, value: str) -> str:
        # View가 아닌 Serializer에서 토큰 검증 (피드백 반영)
        # Redis 캐시에서 purpose=recovery 여부 확인
        # → signup/find_password 등 다른 purpose 토큰이 복구에 사용되지 않도록 구분
        try:
            get_recovery_token_cache(value)
        except InvalidRecoveryTokenError:
            raise serializers.ValidationError("유효하지 않은 복구 토큰입니다.")
        return value
