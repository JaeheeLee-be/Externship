from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.users.models import User, Withdrawal


class WithdrawalListQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False)
    page_size = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(
        required=False,
        choices=tuple(choice[0] for choice in User.Role.choices) + ("TA", "OM", "LC"),
    )
    sort = serializers.ChoiceField(required=False, choices=("latest", "oldest"))


class WithdrawalListUserSerializer(serializers.ModelSerializer[User]):
    role = serializers.ChoiceField(read_only=True, choices=User.Role.choices)
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "role", "position", "birthday"]
        read_only_fields = fields

    def get_position(self, obj: User) -> str | None:
        if _has_related(obj.training_assistants):
            return "TA"
        if _has_related(obj.operation_managers):
            return "OM"
        if _has_related(obj.learning_coachs):
            return "LC"
        if _has_related(obj.cohort_students) or obj.role == User.Role.STUDENT:
            return "ENROLLED"
        return None


class WithdrawalListSerializer(serializers.ModelSerializer[Withdrawal]):
    user = WithdrawalListUserSerializer(read_only=True)
    reason_display = serializers.SerializerMethodField()
    withdrawn_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Withdrawal
        fields = ["id", "user", "reason", "reason_display", "withdrawn_at"]
        read_only_fields = fields

    def get_reason_display(self, obj: Withdrawal) -> str:
        if obj.reason == Withdrawal.Reason.NO_LONGER_NEEDED:
            return "더 이상 필요하지 않음"
        return obj.get_reason_display()


class WithdrawalListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField(read_only=True)
    next = serializers.CharField(read_only=True, allow_null=True)
    previous = serializers.CharField(read_only=True, allow_null=True)
    results = WithdrawalListSerializer(many=True, read_only=True)


def _has_related(manager: Any) -> bool:
    return bool(manager.all())
