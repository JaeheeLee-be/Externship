import math
from typing import Any, NoReturn, cast

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsStudentUser
from apps.qna.exceptions import BaseCustomException
from apps.qna.models import QuestionCategory
from apps.qna.exceptions import BaseCustomException
from apps.qna.schemas.question_schemas import (
    question_create_schema,
    question_detail_schema,
    question_list_schema,
    question_update_schema,
)
from apps.qna.serializers.question_serializers import (
    QuestionCreateResponseSerializer,
    QuestionCreateSerializer,
    QuestionDetailSerializer,
    QuestionListItemSerializer,
    QuestionUpdateResponseSerializer,
    QuestionUpdateSerializer,
)
from apps.qna.services.question_services import (
    QuestionDetailService,
    QuestionListService,
    QuestionService,
)
from apps.users.models import User


class QuestionAPIView(APIView):
    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="로그인한 수강생만 질문을 등록할 수 있습니다.")
        raise PermissionDenied(detail="질문 등록 권한이 없습니다.")

    # ── POST /api/v1/qna/questions ──────────────────────────────────────────────────────
    @question_create_schema
    def post(self, request: Request) -> Response:
        serializer = QuestionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 질문 등록 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = cast(User, request.user)

        question = QuestionService.create_question(
            author=user,
            title=serializer.validated_data["title"],
            content=serializer.validated_data["content"],
            category=serializer.validated_data["category_id"],
            img_urls=serializer.validated_data["img_urls"],
        )

        return Response(
            {
                "message": "질문이 성공적으로 등록되었습니다.",
                "question_id": question.id,
            },
            status=status.HTTP_201_CREATED,
        )

    # ── GET /api/v1/qna/questions ─────────────────────────────────────
    @question_list_schema
    def get(self, request: Request) -> Response:
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = max(1, min(100, int(request.query_params.get("page_size", 10))))
        except ValueError:
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_keyword = request.query_params.get("search_keyword") or None
        answer_status = request.query_params.get("answer_status") or None
        sort = request.query_params.get("sort", "latest")

        raw_category_id = request.query_params.get("category_id")
        category_id: int | None = None
        if raw_category_id:
            try:
                category_id = int(raw_category_id)
            except ValueError:
                return Response(
                    {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not QuestionCategory.objects.filter(id=category_id).exists():
                return Response(
                    {"error_detail": "조회 가능한 질문이 존재하지 않습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        if answer_status and answer_status not in {"answered", "unanswered"}:
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sort not in {"latest", "oldest", "views"}:
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        questions, total_count = QuestionListService.get_question_list(
            page=page,
            page_size=page_size,
            search_keyword=search_keyword,
            category_id=category_id,
            answer_status=answer_status,
            sort=sort,
        )

        results = [QuestionListService.build_result(q) for q in questions]
        serializer = QuestionListItemSerializer(results, many=True)

        total_pages = math.ceil(total_count / page_size) if total_count else 1
        base_url = request.build_absolute_uri(request.path)

        def build_url(p: int) -> str | None:
            if p < 1 or p > total_pages:
                return None
            params = request.query_params.dict()
            params["page"] = str(p)
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            return f"{base_url}?{query_string}"

        return Response(
            {
                "count": total_count,
                "next": build_url(page + 1),
                "previous": build_url(page - 1),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class QuestionDetailAPIView(APIView):
    """질문 상세 조회/수정 API"""

    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="로그인이 필요합니다.")

        # HTTP 메서드에 따라 메시지 구분
        if request.method == "GET":
            raise PermissionDenied(detail="질문 상세 조회 권한이 없습니다.")
        elif request.method == "PUT":
            raise PermissionDenied(detail="질문 수정 권한이 없습니다.")
        else:
            raise PermissionDenied(detail="권한이 없습니다.")

    # ── GET /api/v1/qna/questions/{question_id} ──────────────────────
    @question_detail_schema
    def get(self, request: Request, question_id: int) -> Response:
        """질문 상세 조회"""
        # question_id 유효성 검사
        if not isinstance(question_id, int) or question_id < 1:
            return Response(
                {"error_detail": "유효하지 않은 질문 상세 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = QuestionDetailService.get_question_detail(question_id)
            serializer = QuestionDetailSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseCustomException as e:
            return Response(
                {"error_detail": e.message},
                status=e.status_code,
            )

        # ── PUT /api/v1/qna/questions/{question_id} ───────────────────────
        @question_update_schema
        def put(
            self, request: Request, question_id: int, *args: Any, **kwargs: Any
        ) -> Response:
            """질문 수정"""
            # question_id 유효성 검사
            if not isinstance(question_id, int) or question_id < 1:
                return Response(
                    {"error_detail": "유효하지 않은 질문 수정 요청입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 요청 데이터 검증
            serializer = QuestionUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                first_error = next(iter(serializer.errors.values()))
                error_message = (
                    first_error[0]
                    if isinstance(first_error, list)
                    else str(first_error)
                )
                return Response(
                    {"error_detail": error_message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                # Service에 위임 (비즈니스 로직 제거)
                user = cast(User, request.user)
                updated_question = QuestionService.update_question_by_user(
                    user=user,
                    question_id=question_id,
                    **serializer.validated_data,
                )

                # 응답
                response_data = QuestionUpdateResponseSerializer(
                    {
                        "question_id": updated_question.id,
                        "updated_at": updated_question.updated_at,
                    }
                ).data

                return Response(response_data, status=status.HTTP_200_OK)

            except BaseCustomException as e:
                return Response(
                    {"error_detail": e.message},
                    status=e.status_code,
                )
