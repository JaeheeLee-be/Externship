from typing import Any, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.enrolled_courses_serializer import MyCoursesSerializer
from apps.users.services.enrolled_courses_service import get_my_courses
from apps.users.utils.user_exceptions import NotAuthenticatedError, PermissionDenied


class MyCoursesView(APIView):
    permission_classes: list[Any] = []

    @extend_schema(
        tags=["Accounts (회원관리)"],
        summary="내 수강목록 조회 API",
        description="로그인한 유저의 수강목록만 조회",
        responses={
            200: MyCoursesSerializer(many=True),
            401: OpenApiResponse(description="인증 실패"),
            403: OpenApiResponse(description="수강생 권한 없음"),
        },
    )
    def get(self, request: Request) -> Response:
        try:
            if not request.user.is_authenticated:
                raise NotAuthenticatedError()

            user = cast(User, request.user)

            if user.role != User.Role.STUDENT:
                raise PermissionDenied()

            data = get_my_courses(user)
            serializer = MyCoursesSerializer(data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except NotAuthenticatedError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except PermissionDenied as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
