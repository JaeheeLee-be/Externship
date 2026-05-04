from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.exceptions.admin_exam_deployment_exception import (
    DeploymentConflictError,
    DeploymentDetailNotFoundError,
    DeploymentNoQuestionsError,
    DeploymentNotFoundError,
)
from apps.exams.serializers.admin_exam_deployment_serializer import (
    AdminExamDeploymentCreateSerializer,
    AdminExamDeploymentDetailPathSerializer,
    AdminExamDeploymentDetailSerializer,
    AdminExamDeploymentListQuerySerializer,
    AdminExamDeploymentListResponseSerializer,
    AdminExamDeploymentListSerializer,
)
from apps.exams.services.admin_exam_deployment_service import (
    create_deployment,
    get_deployment_detail,
    get_deployment_list,
)


class AdminExamDeploymentView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(
        self,
        request: Request,
        message: str | None = None,
        code: str | None = None,
    ) -> NoReturn:
        if request.user and request.user.is_authenticated:
            if request.method == "POST":
                raise PermissionDenied("쪽지시험 배포 생성 권한이 없습니다.")
            if request.method == "GET":
                raise PermissionDenied("쪽지시험 배포 목록 조회 권한이 없습니다.")
            raise PermissionDenied("권한이 없습니다.")

        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["exams-deployments"],
        summary="쪽지시험 배포 생성",
        request=AdminExamDeploymentCreateSerializer,
        responses={201: OpenApiResponse(description="pk")},
    )
    def post(self, request: Request) -> Response:
        serializer = AdminExamDeploymentCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 배포 생성 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deployment = create_deployment(serializer.validated_data)
        except DeploymentNoQuestionsError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DeploymentNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except DeploymentConflictError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response({"pk": deployment.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["exams-deployments"],
        summary="쪽지시험 배포 목록 조회",
        responses={200: AdminExamDeploymentListResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        query_serializer = AdminExamDeploymentListQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = get_deployment_list(query_serializer.validated_data)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = AdminExamDeploymentListSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class AdminExamDeploymentDetailView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            if request.method == "GET":
                raise PermissionDenied("쪽지시험 배포 상세 조회 권한이 없습니다.")
            if request.method == "PATCH":
                raise PermissionDenied("쪽지시험 배포 수정 권한이 없습니다.")
            if request.method == "DELETE":
                raise PermissionDenied("배포 삭제 권한이 없습니다.")
            raise PermissionDenied("권한이 없습니다.")

        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    def get(self, request: Request, deployment_id: str) -> Response:
        path_serializer = AdminExamDeploymentDetailPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 배포 상세 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deployment = get_deployment_detail(path_serializer.validated_data["deployment_id"])
            serializer = AdminExamDeploymentDetailSerializer(deployment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DeploymentDetailNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
