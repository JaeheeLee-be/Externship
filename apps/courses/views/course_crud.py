from typing import Any, NoReturn

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.serializers.course_crud import (
    CourseCreateRequestSerializer,
    CourseCreateResponseSerializer,
    CourseDeleteResponseSerializer,
    CourseDetailResponseSerializer,
    CourseListResponseSerializer,
    CourseUpdateRequestSerializer,
    CourseUpdateResponseSerializer,
    ErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)
from apps.courses.services import course_crud as coursecrud_service
from apps.courses.utils.exceptions import (
    CommentPermissionDeniedError,
    CourseAlreadyExistsError,
    CourseNotFoundError,
)


class CourseListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["courses"],
        summary="과정 리스트 조회",
        responses={
            200: CourseListResponseSerializer(many=True),
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        courses = coursecrud_service.get_course_list()
        return Response(
            CourseListResponseSerializer(courses, many=True).data,
            status=status.HTTP_200_OK,
        )


class AdminCourseCreateView(APIView):
    # 어드민만 접근 가능하도록 설정
    permission_classes = [IsAuthenticated, IsAdminUser]

    # 403 처리 - 퍼미션 디나이드
    def permission_denied(self, request: Request, message: Any = None, code: Any = None) -> NoReturn:
        raise CommentPermissionDeniedError()

    @extend_schema(
        tags=["admin-courses"],
        summary="어드민 페이지 과정 등록",
        request=CourseCreateRequestSerializer,
        responses={
            201: CourseCreateResponseSerializer,
            400: ValidationErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = CourseCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course = coursecrud_service.create_course(serializer.validated_data)
        except CourseAlreadyExistsError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CourseCreateResponseSerializer({"detail": "코스가 성공적으로 등록되었습니다.", "id": course.id}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminCourseDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def permission_denied(self, request: Request, message: Any = None, code: Any = None) -> NoReturn:
        raise CommentPermissionDeniedError()

    @extend_schema(
        tags=["admin-courses"],
        summary="어드민 페이지 과정 상세 조회",
        responses={
            200: CourseDetailResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request, course_id: int) -> Response:
        try:
            course = coursecrud_service.get_course_detail(course_id)
        except CourseNotFoundError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CourseDetailResponseSerializer(course).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["admin-courses"],
        summary="어드민 페이지 과정 정보 수정",
        request=CourseUpdateRequestSerializer,
        responses={
            200: CourseUpdateResponseSerializer,
            400: ValidationErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def patch(self, request: Request, course_id: int) -> Response:
        serializer = CourseUpdateRequestSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course = coursecrud_service.update_course(
                course_id=course_id,
                validated_data=serializer.validated_data,
            )
        except CourseNotFoundError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CourseUpdateResponseSerializer(course).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["admin-courses"],
        summary="어드민 페이지 과정 삭제",
        responses={
            200: CourseDeleteResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def delete(self, request: Request, course_id: int) -> Response:
        try:
            coursecrud_service.delete_course(course_id)
        except CourseNotFoundError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CourseDeleteResponseSerializer({"detail": "과정이 삭제되었습니다."}).data,
            status=status.HTTP_200_OK,
        )


class CourseCreateView(APIView):
    # 어드민만 생성 가능하도록 설정
    permission_classes = [IsAuthenticated, IsAdminUser]

    # 403 에러 발생 시 처리
    def permission_denied(self, request: Request, message: Any = None, code: Any = None) -> NoReturn:
        raise CommentPermissionDeniedError()

    def post(self, request: Request) -> Response:
        serializer = CourseCreateRequestSerializer(data=request.data)

        if not serializer.is_valid():
            # 에러 응답 명세 (ValidationErrorResponseSerializer)
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        course = coursecrud_service.create_course(serializer.validated_data)

        # 성공 응답 명세 (CourseCreateResponseSerializer)
        # 메시지를 주어야 하므로 detail 포함
        return Response(
            {"detail": "코스가 성공적으로 생성되었습니다.", "id": course.id}, status=status.HTTP_201_CREATED
        )
