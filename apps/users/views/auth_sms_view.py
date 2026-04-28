from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.auth_sms_serializer import (
    SmsSendSerializer,
    SmsVerifySerializer,
)
from apps.users.services.auth_sms_service import SmsVerificationService
from apps.users.utils.purpose_enum import SmsPurpose


class SmsSendView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Accounts (sms 인증)"],
        summary="sms 인증 코드 발송 API",
        description="회원가입, 이메일 찾기, 전화번호 변경 등 용도(purpose)에 맞는 6자리 sms 인증 코드를 발송합니다.",
        request=SmsSendSerializer,
        responses={
            200: OpenApiResponse(
                description="발송 성공",
                examples=[
                    OpenApiExample(
                        name="성공 응답",
                        value={"detail": "sms 인증 코드가 전송되었습니다."},
                    )
                ],
            ),
            400: OpenApiResponse(
                description="잘못된 요청 (유효성 검사 실패 등)",
                examples=[
                    OpenApiExample(
                        name="실패 응답 (이메일 발송 실패)",
                        value={"error_detail": {"email": ["sms 발송에 실패했습니다. 이메일 주소를 확인해주세요."]}},
                    ),
                    OpenApiExample(
                        name="실패 응답 (형식 오류)",
                        value={"error_detail": {"purpose": ["이 필드는 필수 항목입니다."]}},
                    ),
                ],
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = SmsSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]
        purpose = SmsPurpose(serializer.validated_data["purpose"])

        try:
            SmsVerificationService.send_verification_sms(phone_number, purpose)

            return Response({"detail": "sms 인증코드가 전송되었습니다"})
        except ValidationError as e:
            return Response({"error_detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)


class SmsVerificationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Accounts (sms 인증)"],
        summary="sms 인증 코드 검증 API",
        description="사용자가 입력한 6자리 인증 코드를 검증하고, 성공 시 다음 단계(회원가입 등)를 위한 sms_token을 반환합니다.",
        request=SmsVerifySerializer,
        responses={
            200: OpenApiResponse(
                description="검증 성공",
                examples=[
                    OpenApiExample(
                        name="성공 응답",
                        value={
                            "detail": "sms 인증에 성공하였습니다.",
                            "sms_token": "aB3dE5g7h8i9j0k1l2m3n4o5p6q7r8s9",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="잘못된 요청 (코드 불일치 또는 만료)",
                examples=[
                    OpenApiExample(
                        name="실패 응답 (만료되거나 틀린 코드)",
                        value={"error_detail": {"code": ["인증 코드가 일치하지 않거나 만료되었습니다."]}},
                    )
                ],
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = SmsVerifySerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data["phone_number"]
            code = serializer.validated_data["code"]
            purpose = SmsPurpose(serializer.validated_data.pop("purpose"))

            sms_token = SmsVerificationService.verify_sms_code(phone_number, code, purpose)
            return Response({"detail": "sms 인증이 성공했습니다", "sms_token": sms_token})
        except ValidationError as e:
            return Response({"message": e.detail}, status=status.HTTP_400_BAD_REQUEST)
