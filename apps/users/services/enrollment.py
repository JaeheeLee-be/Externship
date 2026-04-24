from typing import Any

from rest_framework.exceptions import ValidationError

from apps.users.models import StudentEnrollmentRequests, User


def create_enrollment(user: User, validated_data: dict[str, Any]) -> StudentEnrollmentRequests:
    cohort_id = validated_data.get("cohort_id")

    if StudentEnrollmentRequests.objects.filter(user=user, status="pending").exists():
        raise ValidationError("이미 등록 신청중인 내역이 있습니다")

    return StudentEnrollmentRequests.objects.create(
        user=user,
        cohort_id=cohort_id,
        status=StudentEnrollmentRequests.Status.PENDING,
    )
