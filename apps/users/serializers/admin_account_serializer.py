from typing import Any

from rest_framework import serializers

from apps.users.models import User


class AdminAccountQuerySerializer(serializers.Serializer[Any]):

    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)
    search = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=["active", "inactive", "withdrew"], required=False)
    role = serializers.ChoiceField(
        choices=["USER", "ADMIN", "STUDENT"],
        required=False,
    )


class AdminAccountSerializer(serializers.ModelSerializer[User]):

    status = serializers.SerializerMethodField()

    def get_status(self, obj: User) -> str:
        return "ACTIVE" if obj.is_active else "INACTIVE"

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
