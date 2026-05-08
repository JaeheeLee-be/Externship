from __future__ import annotations

from typing import Never, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.withdrawal_serializer import (
    RestoreSerializer,
    WithdrawalSerializer,
)
from apps.users.services.withdrawal_service import restore_user_by_token, withdraw_user
from apps.users.utils.withdrawal_exceptions import (
    WithdrawalBadRequestError,
    WithdrawalNotFoundError,
)
from apps.users.views.user_info_view import UserInfoView


class WithdrawalView(APIView):
    """
    GET/PATCH: UserInfoView 상속 (회원정보 조회/수정)
    DELETE: 회원 탈퇴 - enrollment_url의 UserInfoView와 동일한 'me' 경로를 공유하므로
            __init__.py에서 withdrawal_urls를 먼저 include해 이 View가 우선 매칭됨
    """

    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        super().permission_denied(request, message, code)

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


class RestoreView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["accounts"],
        summary="계정 복구",
        description="이메일 인증 후 발급된 email_token으로 계정을 복구합니다. 토큰은 10분간 유효합니다.",
        request=RestoreSerializer,
        responses={
            200: OpenApiResponse(description="계정 복구 완료"),
            400: inline_serializer(
                name="RestoreValidationError",
                fields={"error_detail": serializers.CharField()},
            ),
            404: inline_serializer(
                name="RestoreNotFound",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = RestoreSerializer(data=request.data)
        # email_token의 존재 여부 및 purpose=recovery 검증은 RestoreSerializer.validate_email_token에서 처리
        # 이메일 인증 코드 발송/검증은 팀원의 EmailSendView, EmailVerificationView에 위임
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 서비스에서 캐시 조회 → 유저 조회(is_active=False) → 계정 복구
            # 복구 완료 후 is_active=True가 되므로 같은 토큰으로 재시도 시 DoesNotExist → DeletedUserError
            restore_user_by_token(serializer.validated_data["email_token"])
        except WithdrawalBadRequestError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except WithdrawalNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "계정복구가 완료되었습니다."}, status=status.HTTP_200_OK)
