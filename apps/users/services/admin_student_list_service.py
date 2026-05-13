from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request

from apps.users.models import User


class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def get_student_list(request: Request) -> tuple[list[User] | None, Pagination]:
    queryset = User.objects.prefetch_related("cohort_students__cohort__course", "withdrawal").order_by("id")

    # 검색 기능(이메일, 이름, 닉네임, 휴대폰번호)
    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search)
            | Q(name__icontains=search)
            | Q(nickname__icontains=search)
            | Q(phone_number__icontains=search)
        )

    # 과정별 필터링
    course_id = request.query_params.get("course_id")
    if course_id:
        queryset = queryset.filter(cohort_students__cohort__course_id=int(course_id)).distinct()

    # 기수별 필터링
    cohort_id = request.query_params.get("cohort_id")
    if cohort_id:
        queryset = queryset.filter(cohort_students__cohort_id=int(cohort_id)).distinct()

    # 상태 표시
    status = request.query_params.get("status")
    if status == "ACTIVATED":
        queryset = queryset.filter(is_active=True, withdrawal__isnull=True)
    elif status == "DEACTIVATED":
        queryset = queryset.filter(is_active=False, withdrawal__isnull=True)
    elif status == "WITHDREW":
        queryset = queryset.filter(withdrawal__isnull=False)

    # 페이지네이션
    paginator = Pagination()
    page = paginator.paginate_queryset(queryset, request)
    return page, paginator
