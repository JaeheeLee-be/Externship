from typing import Any, NoReturn, cast

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsStudentUser
from apps.qna.schemas.question_schemas import (
    question_create_schema,
)
from apps.qna.serializers.question_serializers import (
    QuestionCreateResponseSerializer,
    QuestionCreateSerializer,
)
from apps.qna.services.question_services import QuestionService
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
