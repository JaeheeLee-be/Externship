from __future__ import annotations

from django.db.models import Q
from django.db.models.query import QuerySet

from apps.users.models import User, Withdrawal


def get_withdrawal_list(
    *,
    search: str | None = None,
    role: str | None = None,
    sort: str | None = None,
) -> QuerySet[Withdrawal]:
    queryset = (
        Withdrawal.objects.select_related("user")
        .prefetch_related(
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
