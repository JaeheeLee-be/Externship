from django.db import transaction
from django.utils import timezone

from apps.users.models import CohortStudents, StudentEnrollmentRequests, User


class EnrollmentAcceptError(Exception):
    def __init__(self, invalid_ids: list[int]) -> None:
        self.invalid_ids = invalid_ids
        super().__init__(f"처리할 수 없는 등록 요청 ID가 포함되어 있습니다: {invalid_ids}")


class AdminEnrollmentAcceptService:

    @staticmethod
    @transaction.atomic
    def accept_enrollments(enrollment_ids: list[int]) -> None:
        enrollments = list(
            StudentEnrollmentRequests.objects.select_for_update()
            .filter(id__in=enrollment_ids, status=StudentEnrollmentRequests.Status.PENDING)
            .select_related("user")
        )

        # 요청한 ID 중 존재하지 않거나 PENDING 상태가 아닌 ID 검증
        found_ids = {e.id for e in enrollments}
        invalid_ids = [eid for eid in enrollment_ids if eid not in found_ids]
        if invalid_ids:
            raise EnrollmentAcceptError(invalid_ids)

        now = timezone.now()
        cohort_students = []
        user_ids = []

        for enrollment in enrollments:
            enrollment.status = StudentEnrollmentRequests.Status.ACCEPTED
            enrollment.accepted_at = now
            cohort_students.append(CohortStudents(user=enrollment.user, cohort=enrollment.cohort))
            user_ids.append(enrollment.user_id)

        StudentEnrollmentRequests.objects.bulk_update(enrollments, ["status", "accepted_at"])
        CohortStudents.objects.bulk_create(cohort_students)
        User.objects.filter(id__in=user_ids).update(role=User.Role.STUDENT)
