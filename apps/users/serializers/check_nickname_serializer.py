import re
from typing import Any

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.users.models import User
from apps.users.utils.user_exceptions import DuplicateNicknameError


class CheckNicknameSerializer(ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            "nickname",
        ]
        extra_kwargs: dict[str, Any] = {
            "nickname": {"validators": []}
        }  # 409에러를 400으로 drf unique검사가 먼저 잡아서 건너뛰게 설정

    def validate_nickname(self, value: str) -> str:
        if not re.match(r"^[가-힣a-zA-Z0-9]{2,10}$", value):
            raise serializers.ValidationError("닉네임은 2~10자 이내, 특수문자 제외, 한글/영문/숫자만 허용됩니다.")
        if User.objects.filter(nickname=value).exists():
            raise DuplicateNicknameError()
        return value
