from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.auth_email_serializer import EmailRequestSerializer
from apps.users.serializers.purpose_enum import AuthPurpose
from apps.users.serializers.withdrawal_serializer import RestoreSerializer
from apps.users.services.auth_email_service import EmailVerificationService
from apps.users.services.withdrawal_service import restore_user_by_token
from apps.users.utils.withdrawal_exceptions import (
    WithdrawalBadRequestError,
    WithdrawalNotFoundError,
)


class RestoreRequestView(APIView):
    permission_classes = [AllowAny]

    def handle_exception(self, exc: Exception) -> Response:
        if hasattr(exc, "detail") and hasattr(exc, "status_code"):
            return Response({"error_detail": exc.detail}, status=exc.status_code)  # type: ignore[union-attr]
        return super().handle_exception(exc)

    @extend_schema(
        tags=["accounts"],
        summary="계정 복구 요청",
        description="탈퇴 신청한 이메일로 인증 코드를 발송합니다. 이메일 존재 여부와 무관하게 200을 반환합니다.",
        request=EmailRequestSerializer,
        responses={
            200: OpenApiResponse(description="인증 코드 발송 완료"),
            400: inline_serializer(
                name="RestoreRequestValidationError",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = EmailRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["purpose"] != AuthPurpose.RECOVERY:
            raise ValidationError({"purpose": "계정 복구 요청에는 purpose=recovery만 허용됩니다."})

        email: str = serializer.validated_data["email"]
        try:
            EmailVerificationService.send_verification_email(email, AuthPurpose.RECOVERY)
        except ValidationError:
            pass  # 보안상 이메일 존재 여부 노출 방지

        return Response({"detail": "인증 코드를 이메일로 발송했습니다."}, status=status.HTTP_200_OK)


class RestoreView(APIView):
    permission_classes = [AllowAny]

    def handle_exception(self, exc: Exception) -> Response:
        if hasattr(exc, "detail") and hasattr(exc, "status_code"):
            return Response({"error_detail": exc.detail}, status=exc.status_code)  # type: ignore[union-attr]
        return super().handle_exception(exc)

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
        serializer.is_valid(raise_exception=True)

        try:
            restore_user_by_token(serializer.validated_data["email_token"])
        except WithdrawalBadRequestError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except WithdrawalNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "계정복구가 완료되었습니다."}, status=status.HTTP_200_OK)
