from __future__ import annotations

from django.db import transaction

from apps.users.models import StudentEnrollmentRequests


def reject_student_enrollments(enrollment_ids: list[int]) -> None:
    with transaction.atomic():
        StudentEnrollmentRequests.objects.filter(id__in=enrollment_ids).update(
            status=StudentEnrollmentRequests.Status.REJECTED,
            accepted_at=None,
        )
