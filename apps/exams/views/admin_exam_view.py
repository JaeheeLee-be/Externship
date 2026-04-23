from typing import NoReturn

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.exceptions.exam_exception import ExamTitleConflict, SubjectNotFound
from apps.exams.serializers.admin_exam_serializer import (
    ExamCreateSerializer,
    ExamListSerializer,
)
from apps.exams.services.admin_exam_service import create_exam, get_exam_list


class ExamListCreateView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message=None, code=None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        if request.method == "POST":
            raise PermissionDenied("쪽지시험 생성 권한이 없습니다.")
        raise PermissionDenied("쪽지시험 목록 조회 권한이 없습니다.")

    @extend_schema(
        tags=["exams"],
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
            200: ExamListSerializer,
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 목록 조회 권한이 없습니다."),
        },
    )
    def get(self, request: Request) -> Response:
        try:
            queryset = get_exam_list(
                subject_id=int(request.query_params["subject_id"]) if request.query_params.get("subject_id") else None,
                search_keyword=request.query_params.get("search_keyword"),
                sort=request.query_params.get("sort"),
                order=request.query_params.get("order"),
            )
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(queryset, request)
            serializer = ExamListSerializer(page, many=True, context={"request": request})
        except NotAuthenticated:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}, status=status.HTTP_401_UNAUTHORIZED
            )
        except PermissionDenied:
            return Response({"error_detail": "쪽지시험 목록 조회 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["exams"],
        summary="쪽지 시험 생성",
        description="title은 중복 불가, 이미지 확장자는 jpg, jpeg, png, webp만 가능합니다.",
        request=ExamCreateSerializer,
        responses={
            201: ExamCreateSerializer,
            400: OpenApiResponse(description="유효하지 않은 시험 생성 요청입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 생성 권한이 없습니다."),
            404: OpenApiResponse(description="해당 과목 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="동일한 이름의 시험이 이미 존재합니다."),
        },
    )
    def post(self, request: Request) -> Response:
        try:
            serializer = ExamCreateSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            exam = create_exam(**serializer.validated_data)
        except NotAuthenticated:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}, status=status.HTTP_401_UNAUTHORIZED
            )
        except PermissionDenied:
            return Response({"error_detail": "쪽지시험 생성 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        except ExamTitleConflict:
            return Response({"error_detail": "동일한 이름의 시험이 이미 존재합니다."}, status=status.HTTP_409_CONFLICT)
        except SubjectNotFound:
            return Response({"error_detail": "해당 과목 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response({"error_detail": "유효하지 않은 시험 생성 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ExamCreateSerializer(exam, context={"request": request}).data, status=status.HTTP_201_CREATED)
