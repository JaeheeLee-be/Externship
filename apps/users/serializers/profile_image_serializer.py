from typing import Any

from django.conf import settings
from rest_framework import serializers


class ProfileImageUpdateSerializer(serializers.Serializer[Any]):
    profile_img_url = serializers.URLField(
        allow_null=True,
        error_messages={
            "required": "이 필드는 필수 항목입니다.",
            "invalid": "유효한 URL 형식이어야 합니다.",
        },
    )

    def validate_profile_img_url(self, value: str | None) -> str | None:
        if value is None:
            return value
        bucket = settings.AWS_S3_BUCKET_NAME
        region = settings.AWS_S3_REGION
        if bucket and region:
            expected = f"https://{bucket}.s3.{region}.amazonaws.com/"
            if not value.startswith(expected):
                raise serializers.ValidationError("올바른 S3 이미지 URL이어야 합니다.")
        return value
