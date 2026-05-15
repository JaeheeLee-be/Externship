from pathlib import Path
from typing import Any

from django.utils.text import slugify
from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from apps.core.presigned_url.constants import ALLOWED_SUFFIX


class PresignedUrlRequestSerializer(serializers.Serializer[Any]):
    """
    presigned url 요청 시리얼라이저
    """

    # file_name이 100자 제한이면, img_url이 최대 200자 쯤 나옴
    file_name = serializers.CharField(max_length=100)

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        file_name = attrs["file_name"]

        # 확장자 소문자로 통일
        path = Path(file_name)
        suffix = path.suffix.lower()

        if suffix not in ALLOWED_SUFFIX:
            error = APIException(detail="지원하지 않는 파일 형식입니다.")
            error.status_code = status.HTTP_400_BAD_REQUEST
            raise error

        # 파일명 슬러그화
        stem = path.stem
        slugified_stem = slugify(stem, allow_unicode=True)

        # content_type도 함께 반환
        attrs["file_name"] = slugified_stem + suffix
        attrs["content_type"] = ALLOWED_SUFFIX[suffix]

        return attrs


class PresignedUrlResponseSerializer(serializers.Serializer[Any]):
    """
    presigned url 응답 시리얼라이저
    """

    presigned_url = serializers.CharField()
    img_url = serializers.CharField(max_length=255)
    key = serializers.CharField()
    content_type = serializers.CharField()
