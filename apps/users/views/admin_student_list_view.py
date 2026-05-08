from typing import Never

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.users.models import User
from apps.users.serializers.admin_student_list_serializer import (
    AdminStudentListSerializer,
)


# 페이지네이션
class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminStudentListView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["admin_accounts"],
        summary="어드민 페이지 수강생 목록 조회 API",
        description="관리자 권한을 가진 유저는 어드민 페이지 회원관리메뉴에서 등록된 수강생 목록 조회 가능",
        parameters=[
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="page_size", type=int, required=False),
            OpenApiParameter(name="search", type=str, required=False),
        ],
        responses={
            200: AdminStudentListSerializer(many=True),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
        },
    )
    def get(self, request: Request) -> Response:
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

        # 페이지네이션
        paginator = Pagination()

        try:
            page = paginator.paginate_queryset(queryset, request)
        except Exception:
            return Response({"detail": "유효하지 않은 페이지입니다."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdminStudentListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
