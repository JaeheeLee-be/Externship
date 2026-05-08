from __future__ import annotations

from typing import Any

from rest_framework import serializers


class AdminStudentEnrollmentRejectRequestSerializer(serializers.Serializer[Any]):
    enrollments = serializers.ListField(child=serializers.IntegerField(), required=True)


class AdminStudentEnrollmentRejectResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField(read_only=True)


class AdminStudentEnrollmentErrorSerializer(serializers.Serializer[Any]):
    error_detail = serializers.CharField(read_only=True)


class AdminStudentEnrollmentValidationErrorSerializer(serializers.Serializer[Any]):
    error_detail = serializers.DictField(child=serializers.ListField(child=serializers.CharField()), read_only=True)
