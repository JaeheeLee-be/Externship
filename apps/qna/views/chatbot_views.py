import json
from typing import Any, Callable, Iterator, NoReturn

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.types import AuthenticatedRequest
from apps.qna.exceptions import BaseCustomException
from apps.qna.redis import CacheRepository
from apps.qna.schemas.chatbot_schemas import (
    ai_answer_get_schema,
    ai_answer_post_schema,
    qna_chatbot_get_schema,
    qna_chatbot_post_schema,
)
from apps.qna.serializers.chatbot_serializers import (
    InitialAIAnswerSerializer,
    QNAChatbotListResponseSerializer,
    QNAChatbotRequestSerializer,
    QNAHistoryResponseSerializer,
)
from apps.qna.services.chatbot_services import ChatbotService, InitialService

StreamFn = Callable[[int, int, str], Iterator[str]]


def build_event_stream(user_id: int, question_id: int, message: str, func: StreamFn) -> Iterator[str]:
    for chunk in func(user_id, question_id, message):
        yield f'data: {json.dumps({"message": chunk}, ensure_ascii=False)}\n\n'
    yield "data: [DONE]\n\n"


class InitialAiAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("로그인한 사용자만 요청할 수 있습니다.")
        raise PermissionDenied(message)

    @ai_answer_get_schema
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            instance = InitialService.get_initial_answer(kwargs["question_id"])
            serializer = InitialAIAnswerSerializer(instance=instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)

    @ai_answer_post_schema
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            instance = InitialService.save_initial_answer(kwargs["question_id"])
            serializer = InitialAIAnswerSerializer(instance=instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)
        except Exception:
            return Response(
                {"error_detail": "서버 내부 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QNAChatbotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("로그인한 사용자만 요청할 수 있습니다.")
        raise PermissionDenied(message)

    @qna_chatbot_get_schema
    def get(self, request: AuthenticatedRequest, *args: Any, **kwargs: Any) -> Response:
        try:
            history = ChatbotService.response_qna_history(request.user.id, kwargs["question_id"])
            serializer = QNAHistoryResponseSerializer(history, many=True)
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)

    @qna_chatbot_post_schema
    def post(self, request: AuthenticatedRequest, *args: Any, **kwargs: Any) -> Response | StreamingHttpResponse:
        serializer = QNAChatbotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            ChatbotService.validate_qna_chat(request.user.id, kwargs["question_id"])
            return StreamingHttpResponse(
                build_event_stream(
                    request.user.id,
                    kwargs["question_id"],
                    serializer.validated_data["message"],
                    ChatbotService.response_qna_chat,
                ),
                content_type="text/event-stream",
            )
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)


class QNAChatbotListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("로그인한 사용자만 요청할 수 있습니다.")
        raise PermissionDenied(message)

    def get(self, request: AuthenticatedRequest, *args: Any, **kwargs: Any) -> Response:
        instance = CacheRepository.get_qna_list(request.user.pk)
        serializer = QNAChatbotListResponseSerializer(instance, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)
