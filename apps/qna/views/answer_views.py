from rest_framework import status
from rest_framework.exceptions import (
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.exceptions import ConflictException
from apps.core.utils.types import AuthenticatedRequest
from apps.qna.schemas.answer_schemas import answer_accept_schema, answer_create_schema
from apps.qna.serializers.answer_serializers import (
    AnswerAcceptResponseSerializer,
    AnswerRequestSerializer,
    AnswerResponseSerializer,
)
from apps.qna.services.answer_services import AnswerAcceptService, AnswerService


class AnswerView(APIView):
    """
    POST api/v1/qna/questions/{question_id}/answers
    답변 등록 API
    """

    permission_classes = [IsAuthenticated]
    service = AnswerService()

    @answer_create_schema
    def post(self, request: AuthenticatedRequest, question_id: int) -> Response:
        question = self.service.get_question(question_id)
        serializer = AnswerRequestSerializer(
            data=request.data,
        )
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        answer = self.service.answer_create(
            question_id=question.id,
            user=request.user,
            **serializer.validated_data,
        )
        return Response(AnswerResponseSerializer(answer).data, status=status.HTTP_201_CREATED)


class AnswerAcceptView(APIView):
    """
    POST /api/v1/qna/answers/{answer_id}/accept
    답변 채택에 관한 view
    """

    permission_classes = [IsAuthenticated]
    service = AnswerAcceptService()

    def handle_exception(self, exc: Exception) -> Response:
        if isinstance(exc, NotAuthenticated):
            return Response(
                {"error_detail": "로그인한 사용자만 답변을 채택할 수 있습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return super().handle_exception(exc)

    @answer_accept_schema
    def post(self, request: AuthenticatedRequest, answer_id: int) -> Response:
        try:
            answer = self.service.answer_accept(
                user=request.user,
                answer_id=answer_id,
            )
        except NotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ConflictException as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(AnswerAcceptResponseSerializer(answer).data, status=status.HTTP_200_OK)
