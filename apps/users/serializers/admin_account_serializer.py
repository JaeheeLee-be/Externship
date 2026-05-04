from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.users.models import User


class AdminAccountQuerySerializer(serializers.Serializer[Any]):

    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)
    search = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "inactive", "withdrew"], required=False)
    role = serializers.ChoiceField(
        choices=["user", "admin", "student", "staff"],
        required=False,
    )


class AdminAccountSerializer(serializers.ModelSerializer[User]):

    status = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    def get_status(self, obj: User) -> str:

        try:
            obj.withdrawal  # type: ignore[attr-defined]
            return "withdrew"
        except ObjectDoesNotExist:
            return "active" if obj.is_active else "inactive"

    def get_role(self, obj: User) -> str:

        return obj.role.lower()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "birthday",
            "status",
            "role",
            "created_at",
        ]


class AdminAccountListResponseSerializer(serializers.Serializer[Any]):

    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AdminAccountSerializer(many=True)
