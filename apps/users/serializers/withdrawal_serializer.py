from __future__ import annotations

from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.users.models import Withdrawal
from apps.users.services.withdrawal_service import get_recovery_token_cache
from apps.users.utils.withdrawal_exceptions import InvalidRecoveryTokenError

WITHDRAWAL_REASON_VALUES = [
    "GRADUATION",
    "TRANSFER",
    "NO_LONGER_NEEDED",
    "LACK_OF_INTEREST",
    "TOO_DIFFICULT",
    "FOUND_BETTER_SERVICE",
    "PRIVACY_CONCERNS",
    "POOR_SERVICE_QUALITY",
    "TECHNICAL_ISSUES",
    "LACK_OF_CONTENT",
    "OTHER",
]


@extend_schema_field(
    {
        "type": "string",
        "enum": WITHDRAWAL_REASON_VALUES,
        "description": "탈퇴 사유",
    }
)
class WithdrawalReasonField(serializers.ChoiceField):
    pass


class WithdrawalSerializer(serializers.Serializer[Withdrawal]):
    reason = WithdrawalReasonField(choices=Withdrawal.Reason.choices)
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
