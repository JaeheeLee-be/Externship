from pathlib import Path
from typing import Any

from rest_framework import exceptions, serializers, status

from apps.core.constants import ALLOWED_SUFFIX


class PresignedUrlRequestSerializer(serializers.Serializer[Any]):
    """
    presigned url 요청 시리얼라이저
    """

    # file_name이 100자 제한이면, img_url이 최대 200자 쯤 나옴
    file_name = serializers.CharField(max_length=100)

    def validate_file_name(self, value: str) -> str:
        # 확장자는 소문자로 통일
        suffix = Path(value).suffix.lower()
        stem = Path(value).stem

        if suffix not in ALLOWED_SUFFIX:
            error = exceptions.APIException(detail={"error_detail": "지원하지 않는 파일 형식입니다."})
            error.status_code = status.HTTP_400_BAD_REQUEST
            raise error

        return stem + suffix


class PresignedUrlResponseSerializer(serializers.Serializer[Any]):
    """
    presigned url 응답 시리얼라이저
    """

    presigned_url = serializers.CharField()
    img_url = serializers.CharField(max_length=255)
    key = serializers.CharField()
