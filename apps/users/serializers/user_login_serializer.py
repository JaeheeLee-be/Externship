from typing import Any

from rest_framework import serializers


class LoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenRefreshSerializer(serializers.Serializer[Any]):
    refresh_token = serializers.CharField(
        required=True,
        error_messages={
            "required": "이 필드는 필수 항목입니다.",
        },
    )
