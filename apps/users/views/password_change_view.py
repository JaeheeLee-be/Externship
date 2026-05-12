from typing import Never, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.password_change_serializer import PasswordChangeSerializer
from apps.users.services.password_change_service import PasswordChangeService


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["accounts"],
        summary="비밀번호 재설정 API",
        description="로그인한 유저의 비밀번호를 변경하는 API입니다.",
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(description="비밀번호 변경 성공."),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = cast(User, request.user)
        old_password: str = serializer.validated_data["old_password"]
        new_password: str = serializer.validated_data["new_password"]

        try:
            PasswordChangeService.change_password(user, old_password, new_password)
        except ValueError as e:
            return Response(
                {"error_detail": {"old_password": [str(e)]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "비밀번호 변경 성공."}, status=status.HTTP_200_OK)
