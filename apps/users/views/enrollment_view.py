from typing import Never, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.enrollment_serializer import EnrollmentSerializer
from apps.users.services.enrollment_service import create_enrollment


class EnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        summary="수강생 등록 신청 API",
        description="로그인한 유저만 과정과 기수를 선택하여 수강생 등록 신청할 수 있습니다",
        request=EnrollmentSerializer,
        responses={
            201: OpenApiResponse(description="수강생 등록 신청완료."),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증 실패"),
        },
    )
    def post(self, request: Request) -> Response:
        user = request.user
        serializer = EnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                create_enrollment(user=cast(User, user), validated_data=serializer.validated_data)
                return Response({"detail": "수강생 등록 신청완료."}, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({"error_detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
