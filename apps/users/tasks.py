from __future__ import annotations

from celery import shared_task  # type: ignore[import-untyped]
from django.utils import timezone

from apps.users.models import User, Withdrawal


@shared_task  # type: ignore[misc]
def delete_expired_withdrawn_users() -> int:
    expired_withdrawals = Withdrawal.objects.filter(
        due_date__lte=timezone.localdate(),
        user__isnull=False,
    ).values_list("user_id", flat=True)

    user_ids = list(expired_withdrawals)
    count = len(user_ids)

    if user_ids:
        User.objects.filter(id__in=user_ids).delete()

    return count
