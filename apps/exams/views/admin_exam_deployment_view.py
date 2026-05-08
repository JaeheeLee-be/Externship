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
    DeploymentDeleteConflictError,
    DeploymentDeleteInvalidRequestError,
    DeploymentDeleteNotFoundError,
    DeploymentDetailInvalidRequestError,
    DeploymentDetailNotFoundError,
    DeploymentListInvalidRequestError,
    DeploymentNoQuestionsError,
    DeploymentNotFoundError,
    DeploymentStatusConflictError,
    DeploymentStatusInvalidRequestError,
    DeploymentStatusNotFoundError,
    DeploymentUpdateInvalidRequestError,
    DeploymentUpdateNotFoundError,
)
from apps.exams.serializers.admin_exam_deployment_serializer import (
    AdminExamDeploymentCreateSerializer,
    AdminExamDeploymentDetailPathSerializer,
    AdminExamDeploymentDetailSerializer,
    AdminExamDeploymentListQuerySerializer,
    AdminExamDeploymentListResponseSerializer,
    AdminExamDeploymentListSerializer,
    AdminExamDeploymentStatusResponseSerializer,
    AdminExamDeploymentStatusSerializer,
    AdminExamDeploymentUpdateResponseSerializer,
    AdminExamDeploymentUpdateSerializer,
)
from apps.exams.services.admin_exam_deployment_service import (
    create_deployment,
    delete_deployment,
    get_deployment_detail,
    get_deployment_list,
    update_deployment,
    update_deployment_status,
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
        tags=["exams"],
        summary="쪽지시험 배포 생성",
        request=AdminExamDeploymentCreateSerializer,
        responses={201: OpenApiResponse(description="pk")},
    )
    def post(self, request: Request) -> Response:
        serializer = AdminExamDeploymentCreateSerializer(data=request.data)

        if not serializer.is_valid():
            e = DeploymentNoQuestionsError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        tags=["exams"],
        summary="쪽지시험 배포 목록 조회",
        responses={200: AdminExamDeploymentListResponseSerializer},
    )
    def get(self, request: Request) -> Response:
        query_serializer = AdminExamDeploymentListQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            e = DeploymentListInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        qs = get_deployment_list(query_serializer.validated_data)

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = AdminExamDeploymentListSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)


class AdminExamDeploymentDetailView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            if request.method == "GET":
                raise PermissionDenied("쪽지시험 배포 상세 조회 권한이 없습니다.")
            if request.method == "PATCH":
                raise PermissionDenied("쪽지시험 배포 수정 권한이 없습니다.")
            if request.method == "DELETE":
                raise PermissionDenied("배포 삭제 권한이 없습니다.")
            raise PermissionDenied("권한이 없습니다.")

        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["exams"],
        summary="쪽지시험 배포 상세 조회",
        responses={200: AdminExamDeploymentDetailSerializer},
    )
    def get(self, request: Request, deployment_id: str) -> Response:
        path_serializer = AdminExamDeploymentDetailPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = DeploymentDetailInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            deployment = get_deployment_detail(path_serializer.validated_data["deployment_id"])
        except DeploymentDetailNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminExamDeploymentDetailSerializer(deployment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["exams"],
        summary="쪽지시험 배포 수정",
        request=AdminExamDeploymentUpdateSerializer,
        responses={200: AdminExamDeploymentUpdateResponseSerializer},
    )
    def patch(self, request: Request, deployment_id: str) -> Response:
        path_serializer = AdminExamDeploymentDetailPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = DeploymentUpdateInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AdminExamDeploymentUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            e = DeploymentUpdateInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            deployment = update_deployment(
                deployment_id=path_serializer.validated_data["deployment_id"],
                validated_data=serializer.validated_data,
            )
        except DeploymentUpdateNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            AdminExamDeploymentUpdateResponseSerializer(deployment).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["exams"],
        summary="쪽지시험 배포 삭제",
        responses={200: OpenApiResponse(description="deployment_id")},
    )
    def delete(self, request: Request, deployment_id: str) -> Response:
        path_serializer = AdminExamDeploymentDetailPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = DeploymentDeleteInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        validated_deployment_id = path_serializer.validated_data["deployment_id"]

        try:
            delete_deployment(validated_deployment_id)
        except DeploymentDeleteNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except DeploymentDeleteConflictError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"deployment_id": validated_deployment_id},
            status=status.HTTP_200_OK,
        )


class AdminExamDeploymentStatusView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            raise PermissionDenied("쪽지시험 배포 상태 변경 권한이 없습니다.")
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["exams"],
        summary="쪽지시험 배포 상태 수정",
        request=AdminExamDeploymentStatusSerializer,
        responses={200: AdminExamDeploymentStatusResponseSerializer},
    )
    def patch(self, request: Request, deployment_id: str) -> Response:
        path_serializer = AdminExamDeploymentDetailPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = DeploymentStatusInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        validate_serializer = AdminExamDeploymentStatusSerializer(data=request.data)

        if not validate_serializer.is_valid():
            e = DeploymentStatusInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            deployment = update_deployment_status(
                deployment_id=path_serializer.validated_data["deployment_id"],
                status=validate_serializer.validated_data["status"],
            )
        except DeploymentStatusNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except DeploymentStatusConflictError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(AdminExamDeploymentStatusResponseSerializer(deployment).data, status=status.HTTP_200_OK)
