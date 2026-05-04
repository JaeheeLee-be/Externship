from typing import Any, cast

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.core.utils.permissions import IsStudentUser
from apps.qna.models.question_models import QuestionCategory
from apps.qna.serializers.question_serializers import (
    QuestionCreateResponseSerializer,
    QuestionCreateSerializer,
)
from apps.qna.services.question_services import QuestionService


class QuestionCreateAPIView(APIView):
    permission_classes = [IsStudentUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = QuestionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))
            error_message = first_error[0] if isinstance(first_error, list) else str(first_error)
            return Response(
                {"error_detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = cast(User, request.user)

        category = QuestionCategory.objects.get(id=serializer.validated_data["category_id"])

        question = QuestionService.create_question(
            author=user,
            title=serializer.validated_data["title"],
            content=serializer.validated_data["content"],
            category=category,
            img_urls=serializer.validated_data["img_urls"],
        )

        response_data = QuestionCreateResponseSerializer(
            {"message": "질문이 성공적으로 등록되었습니다.", "question_id": question.id}
        ).data

        return Response(response_data, status=status.HTTP_201_CREATED)
