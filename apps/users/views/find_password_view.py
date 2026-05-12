from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.find_password_serializer import FindPasswordSerializer
from apps.users.services.find_password_service import find_password_service


class FindPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["accounts"],
        summary="비밀번호 분실시 재설정 api",
        description="이메일 인증 후 발급받은 토큰을 활용하여 유저 비밀번호 재설정",
        request=FindPasswordSerializer,
        responses={
            200: OpenApiResponse(description="비밀번호 재설정 성공"),
            400: OpenApiResponse(description="유효성 검사 실패"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = FindPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            find_password_service(serializer.validated_data)

            return Response({"detail": "비밀번호 변경 성공."}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error_detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
