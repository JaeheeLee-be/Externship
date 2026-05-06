from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.users.serializers.admin_detail_serializer import (
    AdminAccountDetailSerializer,
)
from apps.users.services.admin_detail_service import (
    AdminAccountDetailService,
)
from apps.users.utils.admin_exceptions import AdminAccountException


class AdminAccountDetailView(APIView):

    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:

        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise exceptions.PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["admin_accounts"],
        summary="어드민 회원 상세 조회",
        description="어드민 전용 특정 회원의 상세 정보를 조회하는 API입니다.",
        responses={
            200: OpenApiResponse(description="어드민 회원 정보 상세 조회를 성공했습니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
            404: OpenApiResponse(description="사용자 정보를 찾을 수 없습니다."),
        },
    )
    def get(self, request: Request, account_id: int) -> Response:
        try:
            user = AdminAccountDetailService.get_account_detail(account_id)
        except AdminAccountException as exc:
            return Response({"error_detail": exc.detail}, status=exc.status_code)

        serializer = AdminAccountDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
