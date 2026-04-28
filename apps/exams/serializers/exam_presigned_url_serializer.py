from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import APIException

from apps.core.presigned_url.serializers import PresignedUrlRequestSerializer


class ExamErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.CharField()


class ExamPresignedUrlRequestSerializer(PresignedUrlRequestSerializer[dict[str, Any]]):
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            if "file_name" in e.detail:
                error = APIException(detail={"error_detail": str(e.detail["file_name"][0])})
                error.status_code = 400
                raise error
            raise