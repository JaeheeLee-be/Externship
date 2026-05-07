from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.users.serializers.admin_update_serializer import (
    AdminAccountUpdateResponseSerializer,
    AdminAccountUpdateSerializer,
)
from apps.users.services.admin_update_service import (
    AdminAccountUpdateService,
)
from apps.users.utils.admin_exceptions import AdminAccountException


class AdminAccountUpdateView(APIView):

    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:

        if request.authenticators and not request.successful_authenticator:
            raise exceptions.NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise exceptions.PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["admin_accounts"],
        summary="어드민 회원 정보 수정",
        description="어드민 전용 특정 회원의 정보를 수정하는 API입니다.",
        request=AdminAccountUpdateSerializer,
        responses={
            200: OpenApiResponse(description="어드민 회원 수정를 성공했습니다."),
            400: OpenApiResponse(description="11자리 숫자로 구성된 포맷이어야 합니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
            404: OpenApiResponse(description="사용자 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="휴대폰 번호 중복으로 인하여 요청 처리에 실패하였습니다."),
        },
    )
    def patch(self, request: Request, account_id: int) -> Response:
        req_serializer = AdminAccountUpdateSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(
                {"error_detail": req_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = AdminAccountUpdateService.update_account(account_id, req_serializer.validated_data)
        except AdminAccountException as exc:
            return Response({"error_detail": exc.detail}, status=exc.status_code)

        res_serializer = AdminAccountUpdateResponseSerializer(user)
        return Response(res_serializer.data, status=status.HTTP_200_OK)
