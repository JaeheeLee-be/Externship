from typing import Any

from rest_framework import serializers


class AdminEnrollmentAcceptSerializer(serializers.Serializer[Any]):
    enrollments = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
    )
