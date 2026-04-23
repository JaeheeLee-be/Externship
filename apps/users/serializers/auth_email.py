from typing import Any

from rest_framework import serializers


class EmailRequestSerializer(serializers.Serializer[Any]):
    # 인증번호 발송 요청
    email = serializers.EmailField(error_messages={"required": "이 필드는 필수 항목입니다."})
    purpose = serializers.ChoiceField(
        choices=[
            ("signup", "회원가입"),
            ("find_password", "비밀번호 찾기"),
            ("recovery", "계정복구"),
        ],
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )


class EmailVerifySerializer(serializers.Serializer[Any]):
    # 인증번호 확인 요청
    email = serializers.EmailField(error_messages={"required": "이 필드는 필수 항목입니다."})
    code = serializers.CharField(min_length=6, max_length=6, error_messages={"required": "이 필드는 필수 항목입니다."})
