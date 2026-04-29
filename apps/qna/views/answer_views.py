from typing import Any, NoReturn

from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsStudentUser
from apps.core.utils.s3 import PresignedUrlView
from apps.core.utils.types import AuthenticatedRequest
from apps.qna.exceptions import BaseCustomException
from apps.qna.schemas.answer_schemas import answer_accept_schema, answer_create_schema
from apps.qna.serializers.answer_serializers import (
    AnswerAcceptResponseSerializer,
    AnswerRequestSerializer,
    AnswerResponseSerializer,
)
from apps.qna.services.answer_services import AnswerAcceptService, AnswerService


class AnswerPresignedUrlView(PresignedUrlView):
    """post를 불러와 오버라이드 -> 결과적으로 put만 실행"""

    permission_classes: list[type[Any]] = [IsStudentUser]
    path = "uploads/images/answers/"

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class AnswerView(APIView):
    """
    POST api/v1/qna/questions/{question_id}/answers
    답변 등록 API
    """

    permission_classes = [IsStudentUser]
    service = AnswerService()

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user.is_authenticated:
            raise PermissionDenied(detail="답변 작성 권한이 없습니다.")
        raise NotAuthenticated("로그인한 사용자만 답변을 작성할 수 있습니다.")

    @answer_create_schema
    def post(self, request: AuthenticatedRequest, question_id: int) -> Response:
        serializer = AnswerRequestSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        try:
            question = self.service.get_question(question_id)
            answer = self.service.answer_create(
                question_id=question.id,
                user=request.user,
                **serializer.validated_data,
            )
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)
        return Response(AnswerResponseSerializer(answer).data, status=status.HTTP_201_CREATED)


class AnswerAcceptView(APIView):
    """
    POST /api/v1/qna/answers/{answer_id}/accept
    답변 채택에 관한 view
    """

    permission_classes = [IsStudentUser]
    service = AnswerAcceptService()

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user.is_authenticated:
            raise PermissionDenied(detail="답변 채택 권한이 없습니다.")
        raise NotAuthenticated("로그인한 사용자만 답변을 채택할 수 있습니다.")

    @answer_accept_schema
    def post(self, request: AuthenticatedRequest, answer_id: int) -> Response:
        try:
            answer = self.service.answer_accept(
                user=request.user,
                answer_id=answer_id,
            )
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)
        return Response(AnswerAcceptResponseSerializer(answer).data, status=status.HTTP_200_OK)
