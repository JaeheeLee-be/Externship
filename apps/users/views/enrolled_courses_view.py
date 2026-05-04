from typing import Never, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.enrolled_courses_serializer import MyCoursesSerializer
from apps.users.services.enrolled_courses_service import get_my_courses
from apps.users.utils.user_exceptions import NotAuthenticatedError


class MyCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        raise NotAuthenticatedError()

    @extend_schema(
        tags=["Accounts (회원관리)"],
        summary="내 수강목록 조회 API",
        description="로그인한 유저의 수강목록만 조회",
        responses={200: MyCoursesSerializer, 401: OpenApiResponse(description="인증실패")},
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        data = get_my_courses(user)
        serializer = MyCoursesSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
