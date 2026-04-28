from pathlib import Path
from typing import Any

from rest_framework import serializers

PROFILE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class PresignedUrlRequestSerializer(serializers.Serializer[Any]):
    file_name = serializers.CharField(
        error_messages={
            "required": "이 필드는 필수 항목입니다.",
            "blank": "이 필드는 필수 항목입니다.",
        }
    )

    def validate_file_name(self, value: str) -> str:
        if Path(value).suffix.lower() not in PROFILE_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("지원하지 않는 파일 형식입니다.")
        return value


class ProfileImageUpdateSerializer(serializers.Serializer[Any]):
    profile_img_url = serializers.CharField(
        allow_null=True,
        error_messages={"required": "이 필드는 필수 항목입니다."},
    )
