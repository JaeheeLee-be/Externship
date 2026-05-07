from typing import Any, NoReturn

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.exceptions import BaseCustomException
from apps.qna.serializers.chatbot_serializers import InitialAIAnswerSerializer
from apps.qna.services.chatbot_services import InitialService


class InitialAiAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("로그인한 사용자만 요청할 수 있습니다.")
        raise PermissionDenied(message)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            instance = InitialService.get_initial_answer(kwargs["question_id"])
            serializer = InitialAIAnswerSerializer(instance=instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            question_id = kwargs["question_id"]
            instance = InitialService.save_initial_answer_for_created(question_id)
            serializer = InitialAIAnswerSerializer(instance=instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)
