from typing import Any, cast

from rest_framework import status
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
    """JWT 인증 + role이 admin인 경우만 허용"""

    def has_permission(self, request: Request, view: Any) -> bool:
        # IsAuthenticated 체크 먼저 (실패 시 401)
        if not super().has_permission(request, view):
            return False
        # role 체크 (실패 시 403)
        return cast(User, request.user).role == "ADMIN"


class AdminAccountListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request: Request) -> Response:
        # 쿼리 파라미터 검증
        query_serializer = AdminAccountQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # 서비스 호출
        data = AdminAccountService.get_account_list(query_serializer.validated_data)

        # 응답 직렬화
        result_serializer = AdminAccountSerializer(data["results"], many=True)

        # next / previous URL 구성
        base_url = request.build_absolute_uri(request.path)
        page = data["page"]
        page_size = data["page_size"]
        count = data["count"]

        return Response(
            {
                "count": count,
                "next": f"{base_url}?page={page + 1}&page_size={page_size}" if (page * page_size) < count else None,
                "previous": f"{base_url}?page={page - 1}&page_size={page_size}" if page > 1 else None,
                "results": result_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
