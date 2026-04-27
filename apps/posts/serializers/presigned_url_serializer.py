from typing import Any

from rest_framework import serializers


class PresignedUrlRequestSerializer(serializers.Serializer[dict[str, Any]]):
    file_name = serializers.CharField()


class PresignedUrlResponseSerializer(serializers.Serializer[dict[str, Any]]):
    presigned_url = serializers.CharField()
    img_url = serializers.CharField()
    key = serializers.CharField()
