import re
from typing import Any

from rest_framework import serializers

from apps.users.models import User
from apps.users.utils.user_exceptions import DuplicateNicknameError


class CheckNicknameSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField()

    def validate_nickname(self, value: str) -> str:
        clean_value = value.strip()  # 앞뒤공백제거
        if not re.match(r"^[가-힣a-zA-Z0-9]{2,10}$", clean_value):
            raise serializers.ValidationError(
                "닉네임은 2~10자 이내, 특수문자 제외, 공백제외, 한글/영문/숫자만 허용됩니다."
            )
        if User.objects.filter(nickname=clean_value).exists():
            raise DuplicateNicknameError()
        return clean_value
