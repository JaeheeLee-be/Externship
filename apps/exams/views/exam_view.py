from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exams.serializers.exam_serializer import ExamListCreateSerializer
from apps.exams.services.exam_service import get_exam_list


class ExamListCreateView(APIView):
    if not settings.DEBUG:
        permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["exams"],
        summary="쪽지 시험 목록",
        description="쪽지 시험 목록을 출력합니다. filter(subject), search가 포함돼 있습니다.",
        parameters=[
            OpenApiParameter(
                name="subject",
                type=int,
                description="subject의 아이디를 넣어주시면 필터링됩니다.",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="exam의 title과 subject의 title을 동시에 검색하며 유사, 일치를 찾습니다",
            )
        ],
        responses={
            200: ExamListCreateSerializer,
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 목록 조회 권한이 없습니다."),
        }
    )
    def get(self, request):
        queryset = get_exam_list(
            subject=int(request.query_params["subject"]) if request.query_params.get("subject") else None,
            search=request.query_params.get("search"),
        )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ExamListCreateSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["exams"],
        summary="쪽지 시험 생성",
        description="title은 중복 불가, 이미지 확장자는 jpg, jpeg, png, webp만 가능합니다.",
        request=ExamListCreateSerializer,
        responses={
            201: ExamListCreateSerializer,
            400: OpenApiResponse(description="유효하지 않은 시험 생성 요청입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="쪽지시험 생성 권한이 없습니다."),
            404: OpenApiResponse(description="해당 과목 정보를 찾을 수 없습니다."),
            409: OpenApiResponse(description="동일한 이름의 시험이 이미 존재합니다."),

        }
    )
    def post(self, request):
        serializer = ExamListCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
