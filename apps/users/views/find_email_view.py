from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.find_email_serializer import FindEmailSerializer
from apps.users.services.find_email_service import find_email_service


class FindEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["accounts"],
        summary="이메일 찾기 api",
        description="sms 인증 후 발급받은 토큰을 활용하여 이메일 찾기",
        request=FindEmailSerializer,
        responses={
            200: OpenApiResponse(description="이메일 찾기 성공"),
            400: OpenApiResponse(description="유효성 검사 실패"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = FindEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            masked_email = find_email_service(serializer.validated_data)

            return Response(masked_email, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"error_detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
