from django.db import transaction
from django.utils import timezone

from apps.users.models import CohortStudents, StudentEnrollmentRequests, User


class AdminEnrollmentAcceptService:

    @staticmethod
    @transaction.atomic
    def accept_enrollments(enrollment_ids: list[int]) -> None:
        enrollments = (
            StudentEnrollmentRequests.objects.select_for_update()
            .filter(id__in=enrollment_ids, status=StudentEnrollmentRequests.Status.PENDING)
            .select_related("user")
        )

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
