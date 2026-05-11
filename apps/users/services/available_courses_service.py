from django.db.models import QuerySet

from apps.courses.models.cohort import Cohort, StatusChoices
from apps.users.models import StudentEnrollmentRequests, User


def get_available_cohorts(user: User) -> QuerySet[Cohort]:
    """
    요구사항 :
    서버는 수강 신청 가능 상태(모집 중)인 기수만 -> in_progress 필터링하여 반환합니다.
    각 기수는 소속된 과정(Course) 정보와 함께 반환합니다.
    이미 수강 신청 중이거나 수강 중인 기수는 목록에서 제외합니다
    """

    # 이미 수강 신청 중이거나 수강 중인 기수는 추출
    excluded_ids = StudentEnrollmentRequests.objects.filter(
        user=user,
        status__in=[
            StudentEnrollmentRequests.Status.PENDING,
            StudentEnrollmentRequests.Status.ACCEPTED,
        ],
    ).values_list("cohort_id", flat=True)
    """
    ORM 메소드
    - values() : object 원하는 컬럼만 key, value로 가져올수있음
    - values_list() : 튜플 형태 리스트로 가져올수있음(flat인자 사용가능)
    - flat : 리스트 형태로 가져올수있음
    """

    # 모집 중인 기수만 필터링(course join해오기), 위에 추출한 기수 제외
    available_cohorts = (
        Cohort.objects.filter(status__in=[StatusChoices.PREPARING, StatusChoices.IN_PROGRESS])
        .exclude(id__in=excluded_ids)
        .select_related("course")
    )
    return available_cohorts
