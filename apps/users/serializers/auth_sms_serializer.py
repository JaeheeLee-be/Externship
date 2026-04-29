from typing import Any

from rest_framework import serializers

from apps.users.utils.purpose_enum import SmsPurpose


class SmsSendSerializer(serializers.Serializer[Any]):

    phone_number = serializers.CharField(
        max_length=20,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )

    purpose = serializers.ChoiceField(
        choices=SmsPurpose.choices,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )

    def validate_phone_number(self, value: str) -> str:
        # '-'  제거
        clean_value = value.replace("-", "")
        if not clean_value.isdigit():
            raise serializers.ValidationError("전화번호는 숫자여야 합니다.")
        return clean_value


class SmsVerifySerializer(SmsSendSerializer):
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("인증코드는 숫자만 입력되어야 합니다")
        return value
