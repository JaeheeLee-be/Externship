from typing import Any, cast

from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.admin_account_serializer import (
    AdminAccountQuerySerializer,
    AdminAccountSerializer,
)
from apps.users.services.admin_account_service import AdminAccountService


class IsAdminRole(IsAuthenticated):

    def has_permission(self, request: Request, view: Any) -> bool:
        # IsAuthenticated 체크 먼저 (실패 시 401)
        if not super().has_permission(request, view):
            return False
        # role 체크 (실패 시 403)
        return cast(User, request.user).role == "ADMIN"


class AdminAccountListView(APIView):
    permission_classes = [IsAdminRole]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> None:
        """API 명세에 맞춘 에러 응답 형식 오버라이딩"""
        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated({"error_detail": "인증이 필요합니다."})
        raise exceptions.PermissionDenied({"error_detail": message or "접근 권한이 없습니다."})

    def get(self, request: Request) -> Response:
        # 쿼리 파라미터 검증
        query_serializer = AdminAccountQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # 서비스 호출
        data = AdminAccountService.get_account_list(query_serializer.validated_data)

        # 응답 직렬화
        result_serializer = AdminAccountSerializer(data["results"], many=True)

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

        return Response(
            {
                "count": count,
                "next": next_url,
                "previous": previous_url,
                "results": result_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
