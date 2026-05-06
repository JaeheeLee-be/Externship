from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.users.models import User, Withdrawal

ADMIN_USER_ROLE_CHOICES = ("USER", "TA", "OM", "LC", "ADMIN", "STUDENT")
WITHDRAWAL_REASON_DISPLAY_MAP = {
    "NO_LONGER_NEEDED": "더 이상 필요하지 않음",
}


class WithdrawalListQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)
    search = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(required=False, choices=ADMIN_USER_ROLE_CHOICES)
    sort = serializers.ChoiceField(required=False, choices=("latest", "oldest"))


class WithdrawalListUserSerializer(serializers.ModelSerializer[User]):
    role = serializers.ChoiceField(read_only=True, choices=ADMIN_USER_ROLE_CHOICES)

    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "birthday"]
        read_only_fields = fields


class WithdrawalListSerializer(serializers.ModelSerializer[Withdrawal]):
    user = WithdrawalListUserSerializer(read_only=True)
    reason_display = serializers.SerializerMethodField()
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Withdrawal
        fields = ["id", "user", "reason", "reason_display", "withdrawn_at"]
        read_only_fields = fields

    def get_reason_display(self, obj: Withdrawal) -> str:
        return WITHDRAWAL_REASON_DISPLAY_MAP.get(obj.reason, obj.get_reason_display())


class WithdrawalListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField(read_only=True)
    next = serializers.CharField(read_only=True, allow_null=True)
    previous = serializers.CharField(read_only=True, allow_null=True)
    results = WithdrawalListSerializer(many=True, read_only=True)
