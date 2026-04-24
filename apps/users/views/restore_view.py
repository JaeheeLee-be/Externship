from __future__ import annotations

from django.core import signing
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User, Withdrawal
from apps.users.serializers.restore_serializer import RestoreRequestSerializer, RestoreSerializer
from apps.users.services.withdrawal_service import make_restore_token, parse_restore_token, restore_user


class RestoreRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RestoreRequestSerializer

    @extend_schema(
        tags=["accounts"],
        summary="계정 복구 요청",
        description="탈퇴 신청한 이메일로 복구 링크를 발송합니다. 이메일 존재 여부와 무관하게 200을 반환합니다.",
        request=RestoreRequestSerializer,
        responses={200: OpenApiResponse(description="복구 링크 발송 완료")},
    )
    def post(self, request: Request) -> Response:
        serializer = RestoreRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email: str = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            if Withdrawal.objects.filter(user=user).exists():
                token = make_restore_token(user.id)
                # TODO: 이메일 발송 (인증 코드 구현 후 추가)
                # send_restore_email(user.email, token)
                _ = token
        except User.DoesNotExist:
            pass

        return Response({"detail": "복구 링크를 이메일로 발송했습니다."}, status=status.HTTP_200_OK)


class RestoreView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RestoreSerializer

    @extend_schema(
        tags=["accounts"],
        summary="계정 복구",
        description="복구 링크의 토큰으로 계정을 복구합니다. 토큰은 탈퇴 후 14일 이내에만 유효합니다.",
        request=RestoreSerializer,
        responses={
            200: OpenApiResponse(description="계정 복구 완료"),
            400: inline_serializer(
                name="RestoreValidationError",
                fields={"detail": serializers.CharField()},
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = RestoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token: str = serializer.validated_data["token"]
        try:
            user_id: int = parse_restore_token(token)
        except signing.SignatureExpired:
            return Response({"detail": "복구 링크가 만료됐습니다."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({"detail": "유효하지 않은 복구 링크입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "이미 삭제된 계정입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restore_user(user)
        except ValidationError as e:
            return Response({"detail": e.detail[0]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "계정이 복구됐습니다."}, status=status.HTTP_200_OK)
