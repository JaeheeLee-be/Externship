from typing import NoReturn

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.qna.models.question_models import QuestionCategory
from apps.qna.serializers.admin_question_serializers import (
    AdminQuestionListItemSerializer,
    AdminQuestionListQuerySerializer,
)
from apps.qna.services.admin_question_services import AdminQuestionListService


class AdminQuestionListAPIView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="로그인이 필요합니다.")
        raise PermissionDenied(detail="질의응답 목록 조회 권한이 없습니다.")

    def get(self, request: Request) -> Response:
        serializer = AdminQuestionListQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        category_id: int | None = data.get("category_id")

        if category_id and not QuestionCategory.objects.filter(id=category_id).exists():
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        questions, total_count = AdminQuestionListService.get_question_list(
            page=data["page"],
            page_size=data["page_size"],
            search_keyword=data.get("search_keyword") or None,
            category_id=category_id,
            answer_status=data.get("answer_status"),
            sort=data["sort"],
        )

        results = [AdminQuestionListService.build_result(q) for q in questions]

        return Response(
            {
                "page": data["page"],
                "page_size": data["page_size"],
                "total_count": total_count,
                "questions": AdminQuestionListItemSerializer(results, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
