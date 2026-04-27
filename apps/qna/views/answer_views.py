from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.schemas.answer_schemas import answer_accept_schema,answer_create_schema
from apps.core.utils.types import AuthenticatedRequest
from apps.qna.serializers.answer_serializers import (
    AnswerAcceptResponseSerializer,
    AnswerRequestSerializer,
    AnswerResponseSerializer,
)
from apps.qna.services.answer_services import AnswerAcceptService, AnswerService
from apps.users.models import User
from apps.core.utils.permissions import IsRoleAdminUser

class AnswerView(APIView):
    permission_classes = [IsAuthenticated,IsRoleAdminUser]
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
    @answer_accept_schema
    def post(self, request: Request, answer_id: int) -> Response:
        assert isinstance(request.user, User)
        answer = self.service.answer_accept(
            user=request.user,
            answer_id=answer_id,
        )
        return Response(AnswerAcceptResponseSerializer(answer).data, status=status.HTTP_200_OK)
