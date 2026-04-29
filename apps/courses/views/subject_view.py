from typing import Never

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.courses.exceptions import SubjectDuplicateTitleError
from apps.courses.serializers.subject_serializer import (
    SubjectCreateResponseSerializer,
    SubjectCreateSerializer,
    SubjectListSerializer,
)
from apps.courses.services import subject_service


class SubjectListView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated(detail="자격 인증 데이터가 제공되지 않았습니다.", code=code)
        raise exceptions.PermissionDenied(detail="권한이 없습니다.", code=code)

    @extend_schema(
        tags=["Admin - Subject"],
        summary="어드민 과목 목록 조회",
        responses={
            200: SubjectListSerializer(many=True),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="조회 권한이 없습니다."),
        },
    )
    def get(self, request: Request, course_id: int) -> Response:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        total_count, subjects = subject_service.get_subject_list(
            course_id=course_id,
            page=page,
            page_size=page_size,
        )

        base_url = request.build_absolute_uri(request.path)
        next_page = f"{base_url}?page={page + 1}&page_size={page_size}" if (page * page_size) < total_count else None
        previous_page = f"{base_url}?page={page - 1}&page_size={page_size}" if page > 1 else None

        return Response(
            {
                "count": total_count,
                "next": next_page,
                "previous": previous_page,
                "results": SubjectListSerializer(subjects, many=True).data,
            }
        )


class SubjectCreateView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated(detail="자격 인증 데이터가 제공되지 않았습니다.", code=code)
        raise exceptions.PermissionDenied(detail="권한이 없습니다.", code=code)

    @extend_schema(
        tags=["Admin - Subject"],
        summary="어드민 과목 생성",
        request=SubjectCreateSerializer,
        responses={
            201: SubjectCreateResponseSerializer,
            400: OpenApiResponse(description="유효하지 않은 과목 생성입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="과목 생성 권한이 없습니다."),
            404: OpenApiResponse(description="해당 과정을 찾을 수 없습니다."),
            409: OpenApiResponse(description="동일한 이름의 과목이 이미 존재합니다."),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = SubjectCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            subject = subject_service.create_subject(**serializer.validated_data)
        except SubjectDuplicateTitleError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(SubjectCreateResponseSerializer(subject).data, status=status.HTTP_201_CREATED)
