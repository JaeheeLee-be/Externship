import re
from typing import Any

from rest_framework import serializers


class FindPasswordSerializer(serializers.Serializer[Any]):
    email_token = serializers.CharField(required=True, error_messages={"required": "이 필드는 필수 항목입니다."})
    new_password = serializers.CharField(
        write_only=True, required=True, error_messages={"required": "이 필드는 필수 항목입니다."}
    )

    def validate_new_password(self, value: str) -> str:
        if not re.match(r"^\S{6,15}$", value):
            raise serializers.ValidationError("비밀번호는 6~15자여야 합니다.")
        if not re.search(r"[a-zA-Z]", value):
            raise serializers.ValidationError("비밀번호는 영문을 포함해야 합니다.")
        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError("비밀번호는 숫자를 포함해야 합니다.")
        if not re.search(r"[!@#$%^&*]", value):
            raise serializers.ValidationError("비밀번호는 특수문자를 포함해야 합니다.")
        return value
