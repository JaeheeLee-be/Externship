from typing import Any

from rest_framework import serializers

from apps.users.serializers.purpose_enum import AuthPurpose


class EmailRequestSerializer(serializers.Serializer[Any]):
    # 인증번호 발송 요청
    email = serializers.EmailField(error_messages={"required": "이 필드는 필수 항목입니다."})
    purpose = serializers.ChoiceField(
        choices=AuthPurpose.choices,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )


class EmailVerifySerializer(serializers.Serializer[Any]):
    # 인증번호 확인
    email = serializers.EmailField(error_messages={"required": "이 필드는 필수 항목입니다."})
    code = serializers.CharField(min_length=6, max_length=6, error_messages={"required": "이 필드는 필수 항목입니다."})

    def validate_code(self, value: str) -> str:
        if not value.isalnum():
            raise serializers.ValidationError("인증 코드는 영문자와 숫자로만 이루어져야 합니다.")
        return value
