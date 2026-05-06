from django.db.models import QuerySet

from apps.courses.models.cohort import Cohort, StatusChoices
from apps.users.models import StudentEnrollmentRequests, User


def get_my_courses(user: User) -> QuerySet[Cohort]:
    # 본인이 수강 신청하여 승인된 기수 목록을 조회할 수 있어야 합니다.
    # 내 페이지 또는 대시보드에서 현재 수강 중, 수강 예정, 수강 완료된 기수 전체 목록을 확인할 수 있습니다.
    # 각 기수는 소속된 과정(Course) 정보와 함께 반환합니다.

    return Cohort.objects.filter(
        studentenrollmentrequests__user=user,
        studentenrollmentrequests__status=StudentEnrollmentRequests.Status.ACCEPTED,
    ).select_related("course").order_by("-start_date").distinct()