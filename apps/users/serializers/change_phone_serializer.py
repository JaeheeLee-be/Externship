from typing import Any

from rest_framework import serializers


class ChangePhoneSerializer(serializers.Serializer[Any]):
    phone_verify_token = serializers.CharField(
        required=True,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )
