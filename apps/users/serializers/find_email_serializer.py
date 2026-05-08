from typing import Any

from rest_framework import serializers


class FindEmailSerializer(serializers.Serializer[Any]):
    sms_token = serializers.CharField(required=True, error_messages={"required": "이 필드는 필수 항목입니다."})
    name = serializers.CharField(required=True, error_messages={"required": "이 필드는 필수 항목입니다."})


class FindEmailResponseSerializer(serializers.Serializer[Any]):
    email = serializers.CharField()
