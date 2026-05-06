from typing import Any, NoReturn

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.users.serializers.admin_account_serializer import (
    AdminAccountListResponseSerializer,
    AdminAccountQuerySerializer,
)
from apps.users.services.admin_account_service import AdminAccountService


class AdminAccountListView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        """API 명세 에러 메시지 — custom_exception_handler가 error_detail로 변환"""
        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise exceptions.PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["Admin-Accounts"],
        summary="어드민 회원 목록 조회",
        description="어드민 전용 회원 목록 조회 API입니다. 검색, 상태/역할 필터, 페이지네이션을 지원합니다.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                description="페이지 번호 (기본값: 1)",
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                description="페이지당 항목 수 (기본값: 10, 최대: 100)",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="이메일 또는 닉네임으로 검색",
            ),
            OpenApiParameter(
                name="status",
                type=str,
                enum=["active", "inactive", "withdrew"],
                description="회원 상태 필터",
                required=False,
            ),
            OpenApiParameter(
                name="role",
                type=str,
                enum=["user", "admin", "student", "staff"],
                description="회원 역할 필터",
                required=False,
            ),
        ],
        responses={
            200: AdminAccountListResponseSerializer,
            400: OpenApiResponse(description="유효하지 않은 요청 파라미터입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
        },
    )
    def get(self, request: Request) -> Response:
        # 쿼리 파라미터 검증
        query_serializer = AdminAccountQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # 서비스 호출
        data = AdminAccountService.get_account_list(query_serializer.validated_data)

        # next / previous URL 구성 (기존 쿼리파라미터 유지)
        base_url = request.build_absolute_uri(request.path)
        page = data["page"]
        page_size = data["page_size"]
        count = data["count"]

        query_params = request.query_params.copy()
        query_params["page_size"] = str(page_size)

        query_params["page"] = str(page + 1)
        next_url = f"{base_url}?{query_params.urlencode()}" if (page * page_size) < count else None

        query_params["page"] = str(page - 1)
        previous_url = f"{base_url}?{query_params.urlencode()}" if page > 1 else None


        response_serializer = AdminAccountListResponseSerializer(
            {
                "count": count,
                "next": next_url,
                "previous": previous_url,
                "results": data["results"],
            }
        )

        return Response(response_serializer.data, status=status.HTTP_200_OK)
