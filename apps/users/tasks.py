from __future__ import annotations

from celery import shared_task  # type: ignore[import-untyped]
from django.db import transaction
from django.utils import timezone

from apps.users.models import User, Withdrawal


@shared_task  # type: ignore[misc]
def delete_expired_withdrawn_users() -> int:
    # 조회와 삭제 사이에 다른 작업(ex. 계정 복구)이 끼어드는 것을 방지하기 위해 트랜잭션으로 묶음 (피드백 반영)
    with transaction.atomic():
        expired_withdrawals = Withdrawal.objects.filter(
            due_date__lte=timezone.localdate(),
        ).values_list("user_id", flat=True)

        # user가 이미 NULL인 Withdrawal은 삭제 대상에서 제외
        user_ids = [uid for uid in expired_withdrawals if uid is not None]
        count = len(user_ids)

        if user_ids:
            User.objects.filter(id__in=user_ids).delete()

    return count
