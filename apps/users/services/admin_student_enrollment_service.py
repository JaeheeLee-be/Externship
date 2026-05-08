from django.db.models import Q, QuerySet

from apps.users.models import StudentEnrollmentRequests


def get_enrollment_requests(
    status: str | None = None, search: str | None = None, sort: str = "id_asc"
) -> QuerySet[StudentEnrollmentRequests]:
    # N+1 쿼리 방지 모델들을 조인
    queryset = StudentEnrollmentRequests.objects.select_related("user", "cohort", "cohort__course")

    # status 필터링
    if status:
        queryset = queryset.filter(status=status)

    # search 필터링 (이름 또는 이메일 부분 일치)
    if search:
        queryset = queryset.filter(Q(user__name__icontains=search) | Q(user__email__icontains=search))

    # sort 정렬
    if sort == "latest":
        queryset = queryset.order_by("-created_at", "-id")
    elif sort == "oldest":
        queryset = queryset.order_by("created_at", "id")
    else:  # id_asc
        queryset = queryset.order_by("id")

    return queryset
