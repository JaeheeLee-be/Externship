from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import APIException

from apps.core.presigned_url.serializers import PresignedUrlRequestSerializer


class ExamErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.CharField()


# 에러메시지 error_detail로 출력하기 위해 추가
class ExamPresignedUrlRequestSerializer(PresignedUrlRequestSerializer):
    def to_internal_value(self, data: Any) -> Any:
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            detail: Any = e.detail
            if "file_name" in detail:
                error = APIException(detail={"error_detail": str(detail["file_name"][0])})
                error.status_code = 400
                raise error
            raise
