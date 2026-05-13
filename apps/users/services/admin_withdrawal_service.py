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
    position: str | None = None,
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

    # 목록 응답은 user 객체가 필수라서 user가 남아 있는 탈퇴 기록만 대상으로 한다.
    if search:
        queryset = queryset.filter(
            Q(user__email__icontains=search) | Q(user__name__icontains=search) | Q(user__nickname__icontains=search)
        )

    if role:
        queryset = queryset.filter(user__role=role)

    # role은 권한 필드이고, position은 관계 테이블 기준으로 따로 필터링한다.
    if position == "TA":
        queryset = queryset.filter(user__training_assistants__isnull=False)
    elif position == "OM":
        queryset = queryset.filter(user__operation_managers__isnull=False)
    elif position == "LC":
        queryset = queryset.filter(user__learning_coachs__isnull=False)
    elif position == "ENROLLED":
        queryset = queryset.filter(user__cohort_students__isnull=False)

    if sort == "oldest":
        return queryset.distinct().order_by("created_at", "id")
    return queryset.distinct().order_by("-created_at", "-id")


def get_withdrawal_detail(withdrawal_id: int) -> Withdrawal:
    withdrawal = _get_withdrawal_detail_queryset().filter(id=withdrawal_id).first()
    if withdrawal is None:
        raise AdminWithdrawalNotFoundError()
    return withdrawal


def cancel_withdrawal(withdrawal_id: int) -> None:
    # 탈퇴 기록 삭제와 계정 활성화는 함께 성공해야 하므로 하나의 트랜잭션으로 묶는다.
    with transaction.atomic():
        withdrawal = Withdrawal.objects.select_related("user").filter(id=withdrawal_id, user__isnull=False).first()
        if withdrawal is None or withdrawal.user is None:
            raise AdminWithdrawalNotFoundError()
        user = withdrawal.user
        withdrawal.delete()
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])


def _get_withdrawal_detail_queryset() -> QuerySet[Withdrawal]:
    # 상세 응답에서 user, position, assigned_courses를 만들 때 필요한 관계를 미리 가져온다.
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
