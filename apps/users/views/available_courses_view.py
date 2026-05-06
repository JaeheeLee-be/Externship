from typing import Never, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.available_courses_serializer import (
    AvailableCoursesSerializer,
)
from apps.users.services.available_courses_service import get_available_cohorts


class AvailableCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["Accounts (회원관리)"],
        summary="수강신청 가능한 기수 조회 API",
        description="모집 중인 기수만 소속된 과정 정보와 함께 반환합니다",
        responses={200: AvailableCoursesSerializer, 401: OpenApiResponse(description="인증실패")},
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        data = get_available_cohorts(user)
        serializer = AvailableCoursesSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
