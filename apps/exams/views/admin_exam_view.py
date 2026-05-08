from typing import Any, NoReturn

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.exceptions.exam_exception import (
    ExamDeleteConflict,
    ExamTitleConflict,
    SubjectNotFound,
)
from apps.exams.serializers.admin_exam_serializer import (
    ExamCreatePutSerializer,
    ExamDeleteResponseSerializer,
    ExamDetailSerializer,
    ExamErrorSerializer,
    ExamListQuerySerializer,
    ExamListSerializer,
    ExamPageResponseSerializer,
    ExamValidationErrorSerializer,
)
from apps.exams.services.admin_exam_service import (
    create_exam,
    delete_exam,
    get_exam,
    get_exam_list,
    put_exam,
)


class CustomExamPagination(PageNumberPagination):
    def get_paginated_response(self, data: ReturnList[Any] | ReturnDict[str, Any]) -> Response:
        assert self.page is not None
        return Response(
            {"page": self.page.number, "size": self.page_size, "total_count": self.page.paginator.count, "exams": data}
        )


class ExamListCreateView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        if request.method == "POST":
            raise PermissionDenied("쪽지시험 생성 권한이 없습니다.")
        raise PermissionDenied("쪽지시험 목록 조회 권한이 없습니다.")

    @extend_schema(
        tags=["admin-exams"],
        summary="쪽지 시험 목록",
        description="쪽지 시험 목록을 출력합니다. filter(subject), search가 포함돼 있습니다.",
        parameters=[
            OpenApiParameter(
                name="subject_id",
                type=int,
                description="subject의 아이디를 넣어주시면 필터링됩니다.",
            ),
            OpenApiParameter(
                name="search_keyword",
                type=str,
                description="exam의 title과 subject의 title을 동시에 검색하며 유사, 일치를 찾습니다",
            ),
            OpenApiParameter(
                name="sort",
                type=str,
                description="id, title, subject__title, question_count, "
                "submit_count, created_at, updated_at 값 중 선택 가능",
            ),
            OpenApiParameter(
                name="order",
                type=str,
                description="asc, desc 값 중 선택 가능",
            ),
        ],
        responses={
            200: ExamPageResponseSerializer,
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 목록 조회 권한이 없습니다."),
        },
    )
    def get(self, request: Request) -> Response:
        query_serializer = ExamListQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response({"error_detail": query_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        queryset = get_exam_list(
            subject_id=query_serializer.validated_data.get("subject_id"),
            search_keyword=request.query_params.get("search_keyword"),
            sort=request.query_params.get("sort"),
            order=request.query_params.get("order"),
        )
        paginator = CustomExamPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ExamListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["admin-exams"],
        summary="쪽지 시험 생성",
        description="title은 중복 불가, 이미지 확장자는 jpg, jpeg, png, webp, gif만 가능합니다.",
        request=ExamCreatePutSerializer,
        responses={
            201: ExamCreatePutSerializer,
            400: OpenApiResponse(
                description="유효하지 않은 시험 생성 요청입니다.",
                response=ExamValidationErrorSerializer,
            ),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 생성 권한이 없습니다."),
            404: OpenApiResponse(description="해당 과목 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="동일한 이름의 시험이 이미 존재합니다."),
        },
    )
    def post(self, request: Request) -> Response:
        try:
            serializer = ExamCreatePutSerializer(data=request.data, context={"request": request})
            if not serializer.is_valid():
                return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            exam = create_exam(**serializer.validated_data)
        except ExamTitleConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except SubjectNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            ExamCreatePutSerializer(exam, context={"request": request}).data, status=status.HTTP_201_CREATED
        )


class ExamDetailView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        if request.method == "GET":
            raise PermissionDenied("쪽지시험 상세 조회 권한이 없습니다.")
        if request.method == "PUT":
            raise PermissionDenied("쪽지시험 수정 권한이 없습니다.")
        raise PermissionDenied("쪽지시험 삭제 권한이 없습니다.")

    @extend_schema(
        tags=["admin-exams"],
        summary="쪽지 시험 상세 조회",
        responses={
            200: ExamDetailSerializer,
            401: ExamErrorSerializer,
            403: OpenApiResponse(response=ExamErrorSerializer, description="쪽지시험 상세 조회 권한이 없습니다."),
            404: OpenApiResponse(response=ExamErrorSerializer, description="해당 쪽지시험 정보를 찾을 수 없습니다."),
        },
    )
    def get(self, request: Request, exam_id: int) -> Response:
        try:
            exam = get_exam(exam_id)
            serializer = ExamDetailSerializer(exam, context={"request": request})
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["admin-exams"],
        summary="쪽지 시험 수정",
        description="title은 중복 불가, 이미지 확장자는 jpg, jpeg, png, webp, gif만 가능합니다.",
        request=ExamCreatePutSerializer,
        responses={
            200: ExamCreatePutSerializer,
            400: OpenApiResponse(
                description="유효하지 않은 요청 데이터입니다.",
                response=ExamValidationErrorSerializer,
            ),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 수정 권한이 없습니다."),
            404: OpenApiResponse(
                description="해당 쪽지시험 정보를 찾을 수 없습니다. | 해당 과목 정보를 찾을 수 없습니다.",
                response=ExamErrorSerializer,
            ),
            409: OpenApiResponse(
                description="동일한 이름의 시험이 이미 존재합니다.",
                response=ExamErrorSerializer,
            ),
        },
    )
    def put(self, request: Request, exam_id: int) -> Response:
        try:
            serializer = ExamCreatePutSerializer(data=request.data, context={"request": request})
            if not serializer.is_valid():
                return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            exam = put_exam(exam_id=exam_id, **serializer.validated_data)
        except ExamTitleConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except SubjectNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ExamCreatePutSerializer(exam, context={"request": request}).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["admin-exams"],
        summary="쪽지 시험 삭제",
        responses={
            200: ExamDeleteResponseSerializer,
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(response=ExamErrorSerializer, description="쪽지시험 삭제 권한이 없습니다."),
            404: OpenApiResponse(
                response=ExamErrorSerializer, description="삭제하려는 쪽지시험 정보를 찾을 수 없습니다."
            ),
            409: OpenApiResponse(response=ExamErrorSerializer, description="쪽지시험 삭제 중 충돌이 발생했습니다."),
        },
    )
    def delete(self, request: Request, exam_id: int) -> Response:
        try:
            delete_exam(exam_id)
        except ExamDeleteConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(ExamDeleteResponseSerializer({"id": exam_id}).data, status=status.HTTP_200_OK)
