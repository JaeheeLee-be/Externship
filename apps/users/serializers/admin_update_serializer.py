import re
from typing import Any

from rest_framework import serializers

from apps.users.models import User


class AdminAccountUpdateSerializer(serializers.Serializer[Any]):
    nickname = serializers.CharField(max_length=10, required=False)
    name = serializers.CharField(max_length=30, required=False)
    phone_number = serializers.CharField(required=False)
    birthday = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=User.Gender.choices, required=False)
    profile_img_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)

    @staticmethod
    def validate_phone_number(value: str) -> str:
        if not re.fullmatch(r"\d{11}", value):
            raise serializers.ValidationError("11자리 숫자로 구성된 포맷이어야 합니다.")
        return value


class AdminAccountUpdateResponseSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "profile_img_url",
            "updated_at",
        ]
        read_only_fields = fields
