from __future__ import annotations

from datetime import date

from celery import shared_task  # type: ignore[import-untyped]

from apps.users.models import Withdrawal


@shared_task  # type: ignore[misc]
def delete_expired_withdrawn_users() -> int:
    expired_withdrawals = Withdrawal.objects.filter(
        due_date__lte=date.today(),
    ).select_related("user")

    count = 0
    for withdrawal in expired_withdrawals:
        withdrawal.user.delete()  # user 삭제 → withdrawal.user = NULL (SET_NULL)
        count += 1

    return count
