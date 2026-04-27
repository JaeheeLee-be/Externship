from typing import Any

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.users.models import StudentEnrollmentRequests, User


# exists()와 create() 중 하나라도 실패하면 전체 취소
@transaction.atomic
def create_enrollment(user: User, validated_data: dict[str, Any]) -> StudentEnrollmentRequests:
    cohort_id = validated_data.get("cohort_id")

    if (
        StudentEnrollmentRequests.objects.select_for_update()
        .filter(user=user, status=StudentEnrollmentRequests.Status.PENDING)
        .exists()
    ):
        raise ValidationError("이미 등록 신청중인 내역이 있습니다")

    return StudentEnrollmentRequests.objects.create(
        user=user,
        cohort_id=cohort_id,
        status=StudentEnrollmentRequests.Status.PENDING,
    )