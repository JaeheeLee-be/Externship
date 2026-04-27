from __future__ import annotations

from rest_framework import serializers


class RestoreRequestSerializer(serializers.Serializer[None]):
    email = serializers.EmailField()


class RestoreSerializer(serializers.Serializer[None]):
    email_token = serializers.CharField()
