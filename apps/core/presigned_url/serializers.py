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


    def validate(self, attrs: dict) -> dict:
        file_name = attrs["file_name"]

        path = Path(file_name)
        suffix = path.suffix.lower()

        if suffix not in ALLOWED_SUFFIX:
            error = exceptions.APIException(detail={"error_detail": "지원하지 않는 파일 형식입니다."})
            error.status_code = status.HTTP_400_BAD_REQUEST
            raise error

        stem = path.stem

        attrs["file_name"] = stem + suffix
        attrs["content_type"] = ALLOWED_SUFFIX[suffix]

        return attrs



class PresignedUrlResponseSerializer(serializers.Serializer[Any]):
    """
    presigned url 응답 시리얼라이저
    """

    presigned_url = serializers.CharField()
    img_url = serializers.CharField(max_length=255)
    key = serializers.CharField()
