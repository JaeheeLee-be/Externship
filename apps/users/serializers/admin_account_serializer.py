from typing import Any

from rest_framework import serializers

from apps.users.models import User


class AdminAccountQuerySerializer(serializers.Serializer[Any]):
    """어드민 회원 목록 조회 쿼리 파라미터 검증용"""

    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)
    search = serializers.CharField(required=False, allow_blank=True)

    status = serializers.ChoiceField(
        choices=["active", "inactive", "withdrew"],
        required=False,
    )

    role = serializers.ChoiceField(
        choices=["user", "staff", "admin", "student"],
        required=False,
    )


class AdminAccountSerializer(serializers.ModelSerializer[User]):
    """어드민 회원 목록 응답 직렬화용 (기존과 동일)"""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "birthday",
            "is_active",
            "role",
            "created_at",
        ]
