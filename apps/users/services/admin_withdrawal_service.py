from __future__ import annotations

from django.db.models import Q
from django.db.models.query import QuerySet

from apps.users.models import Withdrawal


def get_withdrawal_list(
    *,
    search: str | None = None,
    role: str | None = None,
    sort: str | None = None,
) -> QuerySet[Withdrawal]:
    queryset = Withdrawal.objects.select_related("user").filter(user__isnull=False)

    if search:
        queryset = queryset.filter(
            Q(user__email__icontains=search) | Q(user__name__icontains=search) | Q(user__nickname__icontains=search)
        )

    if role:
        queryset = queryset.filter(user__role=role)

    if sort == "oldest":
        return queryset.order_by("created_at", "id")
    return queryset.order_by("-created_at", "-id")
