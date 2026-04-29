from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.serializers.course_crud import (
    # CourseActionResponseSerializer,
    CourseDetailResponseSerializer,
    CourseListResponseSerializer,
    CourseRequestSerializer,
)
from apps.posts.services import course_crud as coursecrud_service
from posts.exceptions import CourseNotFoundError


class CourseListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["courses"],
        summary="과정 목록 조회",
        responses={200: CourseListResponseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        courses = coursecrud_service.list_courses()
        return Response(
            CourseListResponseSerializer(courses, many=True).data,
            status=status.HTTP_200_OK,
        )


class CourseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["courses"],
        summary="과정 등록",
        request=CourseRequestSerializer,
        responses={
            201: CourseDetailResponseSerializer,
            # 400: CourseActionResponseSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = CourseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = coursecrud_service.create_course(serializer.validated_data)

        return Response(
            CourseDetailResponseSerializer(course).data,
            status=status.HTTP_201_CREATED,
        )


class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["courses"],
        summary="과정 상세 조회",
        responses={
            200: CourseDetailResponseSerializer,
            # 404: CourseActionResponseSerializer,
        },
    )

    def get(self, request: Request, course_id: int) -> Response:
        try:
            course = coursecrud_service.get_course(course_id) #미완성
        except CourseNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class CourseUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["courses"],
        summary="과정 수정",
        request=CourseRequestSerializer,
        responses={
            200: CourseDetailResponseSerializer,
            400: CourseActionResponseSerializer,
            404: CourseActionResponseSerializer,
        },
    )
    def put(self, request: Request, course_id: int) -> Response:
        serializer = CourseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = coursecrud_service.update_course(
            course_id=course_id,
            validated_data=serializer.validated_data,
        )

        return Response(
            CourseDetailResponseSerializer(course).data,
            status=status.HTTP_200_OK,
        )


class CourseDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["courses"],
        summary="과정 삭제",
        responses={
            200: CourseActionResponseSerializer,
            400: CourseActionResponseSerializer,
            404: CourseActionResponseSerializer,
        },
    )
    def delete(self, request: Request, course_id: int) -> Response:
        coursecrud_service.delete_course(course_id)

        return Response(
            CourseActionResponseSerializer({"detail": "과정이 삭제되었습니다."}).data,
            status=status.HTTP_200_OK,
        )
