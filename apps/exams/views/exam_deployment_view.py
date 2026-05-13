from typing import Any, NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsStudentUser
from apps.exams.exceptions.exam_deployment_exception import (
    ExamDeploymentCodeMismatchError,
    ExamDeploymentExpiredError,
    ExamDeploymentInfoNotFoundError,
    ExamDeploymentInvalidRequestError,
    ExamDeploymentNotFoundError,
    ExamDeploymentNotYetOpenError,
    ExamDeploymentUserNotFoundError,
    ExamDeploymentYetExpiredError,
)
from apps.exams.serializers.exam_deployment_serializer import (
    ExamDeploymentCheckSerializer,
    ExamDeploymentDetailSerializer,
    ExamDeploymentListQuerySerializer,
    ExamDeploymentListSerializer,
    ExamDeploymentPathSerializer,
    ExamDeploymentStatusSerializer,
)
from apps.exams.services.exam_deployment_service import (
    check_deployment_code,
    get_deployment_detail_for_user,
    get_deployment_list_for_user,
    get_deployment_status_for_user,
)


# TODO : 페이지네이션이 달라 커스텀 제작 후 사용 core/utils에 분리해도 되는 지 확인 후 수정
class ExamDeploymentPagination(PageNumberPagination):
    def get_paginated_response(self, data: Any) -> Response:
        assert self.page is not None
        return Response(
            {
                "page": self.page.number,
                "has_next": self.page.has_next(),
                "results": data,
            }
        )


class ExamDeploymentListView(APIView):
    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            raise PermissionDenied("권한이 없습니다.")
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["user-exams"],
        summary="쪽지시험 목록 조회",
        responses={200: ExamDeploymentListSerializer},
    )
    def get(self, request: Request) -> Response:
        query_serializer = ExamDeploymentListQuerySerializer(data=request.query_params)

        if not query_serializer.is_valid():
            e = ExamDeploymentInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            exam_list = get_deployment_list_for_user(request.user, query_serializer.validated_data["status"])
        except ExamDeploymentUserNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        paginator = ExamDeploymentPagination()
        page: list[Any] | None = paginator.paginate_queryset(exam_list, request)  # type: ignore[arg-type]
        serializer = ExamDeploymentListSerializer(page or exam_list, many=True)
        return paginator.get_paginated_response(serializer.data)


class ExamDeploymentCheckCodeView(APIView):
    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            raise PermissionDenied("시험에 응시할 권한이 없습니다.")
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["user-exams"],
        summary="쪽지시험 참가 코드 검증",
        request=ExamDeploymentCheckSerializer,
        responses={204: OpenApiResponse(description="응시 코드 확인 성공")},
    )
    def post(self, request: Request, deployment_id: str) -> Response:
        path_serializer = ExamDeploymentPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = ExamDeploymentInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        body_serializer = ExamDeploymentCheckSerializer(data=request.data)
        # TODO : 명세서상에 400에러메세지가 하나밖에 있지 않아 시리얼라이즈에 타입검증과 서비스에 비교연산검증을 하나의 custum exception으로 처리
        # 상태코드와 에러메세지가 같아 사실상 구분이 어렵습니다. 이 부분 확인 후 피드백 주시면 수정하겠습니다.
        if not body_serializer.is_valid():
            code_error = ExamDeploymentCodeMismatchError()
            return Response({"error_detail": str(code_error)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            check_deployment_code(
                request.user,
                path_serializer.validated_data["deployment_id"],
                body_serializer.validated_data["code"],
            )
        except ExamDeploymentNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ExamDeploymentCodeMismatchError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ExamDeploymentNotYetOpenError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_423_LOCKED)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ExamDeploymentDetailView(APIView):
    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            raise PermissionDenied("권한이 없습니다.")
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["user-exams"],
        summary="쪽지시험 응시 문제풀이",
        responses={200: ExamDeploymentDetailSerializer},
    )
    def get(self, request: Request, deployment_id: str) -> Response:
        path_serializer = ExamDeploymentPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = ExamDeploymentInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        validated_deployment_id = path_serializer.validated_data["deployment_id"]

        try:
            deployment, answer_json = get_deployment_detail_for_user(request.user, validated_deployment_id)
        except ExamDeploymentInfoNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ExamDeploymentExpiredError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_410_GONE)

        serializer = ExamDeploymentDetailSerializer(deployment, context={"answer_json": answer_json})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExamDeploymentStatusView(APIView):
    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user and request.user.is_authenticated:
            raise PermissionDenied("권한이 없습니다.")
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["user-exams"],
        summary="쪽지시험 상태 확인",
        responses={200: ExamDeploymentStatusSerializer},
    )
    def get(self, request: Request, deployment_id: str) -> Response:
        path_serializer = ExamDeploymentPathSerializer(data={"deployment_id": deployment_id})

        if not path_serializer.is_valid():
            e = ExamDeploymentInvalidRequestError()
            return Response({"error_detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = get_deployment_status_for_user(
                request.user,
                path_serializer.validated_data["deployment_id"],
            )
        # TODO : 명세서 응답 예시에는 만료/비활성화 시 200 {"exam_status": "closed", "force_submit": true} 반환으로 되어있으나
        # 에러코드에 410이 존재하여 현재는 410으로 처리. 410명확한 케이스 정해지면 피드백 후 수정 예정.
        except ExamDeploymentInfoNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ExamDeploymentYetExpiredError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_410_GONE)

        serializer = ExamDeploymentStatusSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)
