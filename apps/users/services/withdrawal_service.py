from __future__ import annotations

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.users.models import User, Withdrawal


def withdraw_user(user: User, reason: str, reason_detail: str = "") -> Withdrawal:
    try:
        with transaction.atomic():
            if Withdrawal.objects.filter(user=user).exists():
                raise ValidationError("이미 탈퇴 신청한 계정입니다.")
            due_date = date.today() + timedelta(weeks=2)
            withdrawal = Withdrawal.objects.create(
                user=user,
                reason=reason,
                reason_detail=reason_detail,
                due_date=due_date,
            )
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
            return withdrawal
    except IntegrityError:
        raise ValidationError("이미 탈퇴 신청한 계정입니다.")


def restore_user(user: User) -> None:
    with transaction.atomic():
        Withdrawal.objects.filter(user=user).delete()
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])
