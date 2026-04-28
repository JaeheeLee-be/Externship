from __future__ import annotations

from typing import Never, Optional, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.withdrawal_serializer import WithdrawalSerializer
from apps.users.services.withdrawal_service import withdraw_user
from apps.users.utils.withdrawal_exceptions import WithdrawalBadRequestError


class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(
        self,
        request: Request,
        message: Optional[str] = None,
        code: Optional[str] = None,
    ) -> Never:
        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("접근 권한이 없습니다.")

    @extend_schema(
        tags=["accounts"],
        summary="회원 탈퇴",
        description="탈퇴 신청 후 2주간 데이터가 보관되며, 2주 내 계정 복구가 가능합니다. 2주 후 완전 삭제됩니다.",
        request=WithdrawalSerializer,
        responses={
            204: OpenApiResponse(description="탈퇴 처리 완료"),
            400: inline_serializer(
                name="WithdrawalValidationError",
                fields={"error_detail": serializers.CharField(required=False)},
            ),
            401: inline_serializer(
                name="WithdrawalUnauthorized",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def delete(self, request: Request) -> Response:
        serializer = WithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            withdraw_user(
                user=cast(User, request.user),
                reason=serializer.validated_data["reason"],
                reason_detail=serializer.validated_data["reason_detail"],
            )
        except WithdrawalBadRequestError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
