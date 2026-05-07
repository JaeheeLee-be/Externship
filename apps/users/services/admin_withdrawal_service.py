from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet

from apps.users.models import User, Withdrawal


class AdminWithdrawalNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("회원탈퇴 정보를 찾을 수 없습니다.")


def get_withdrawal_list(
    *,
    search: str | None = None,
    role: str | None = None,
    sort: str | None = None,
) -> QuerySet[Withdrawal]:
    queryset = (
        Withdrawal.objects.select_related("user")
        .prefetch_related(
            "user__cohort_students",
            "user__training_assistants",
            "user__operation_managers",
            "user__learning_coachs",
        )
        .filter(user__isnull=False)
    )

    if search:
        queryset = queryset.filter(
            Q(user__email__icontains=search) | Q(user__name__icontains=search) | Q(user__nickname__icontains=search)
        )

    if role == "TA":
        queryset = queryset.filter(user__training_assistants__isnull=False)
    elif role == "OM":
        queryset = queryset.filter(user__operation_managers__isnull=False)
    elif role == "LC":
        queryset = queryset.filter(user__learning_coachs__isnull=False)
    elif role in User.Role.values:
        queryset = queryset.filter(user__role=role)

    if sort == "oldest":
        return queryset.distinct().order_by("created_at", "id")
    return queryset.distinct().order_by("-created_at", "-id")


def get_withdrawal_detail(withdrawal_id: int) -> Withdrawal:
    withdrawal = _get_withdrawal_detail_queryset().filter(id=withdrawal_id).first()
    if withdrawal is None:
        raise AdminWithdrawalNotFoundError()
    return withdrawal


def cancel_withdrawal(withdrawal_id: int) -> None:
    with transaction.atomic():
        withdrawal = Withdrawal.objects.select_related("user").filter(id=withdrawal_id, user__isnull=False).first()
        if withdrawal is None or withdrawal.user is None:
            raise AdminWithdrawalNotFoundError()
        user = withdrawal.user
        withdrawal.delete()
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])


def _get_withdrawal_detail_queryset() -> QuerySet[Withdrawal]:
    return (
        Withdrawal.objects.select_related("user")
        .prefetch_related(
            "user__cohort_students__cohort__course",
            "user__training_assistants__cohort__course",
            "user__operation_managers__course__cohorts",
            "user__learning_coachs__course__cohorts",
        )
        .filter(user__isnull=False)
    )
