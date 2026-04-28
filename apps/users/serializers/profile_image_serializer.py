from typing import Any

from rest_framework import serializers


class ProfileImageUpdateSerializer(serializers.Serializer[Any]):
    profile_img_url = serializers.CharField(
        allow_null=True,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )
