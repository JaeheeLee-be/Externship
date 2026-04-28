from typing import Any

from rest_framework import serializers


class ExamErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.CharField()
