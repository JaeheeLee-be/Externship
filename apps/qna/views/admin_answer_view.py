from typing import NoReturn

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.qna.exceptions import BaseCustomException
from apps.qna.schemas.answer_admin_schemas import answer_admin_delete_schema
from apps.qna.serializers.admin_answer_serializers import AdminAnswerDeleteSerializer
from apps.qna.services.admin_answer_service import AdminAnswerDeleteService


class AdminAnswerDeleteView(APIView):
    """
    DELETE api/v1/admin/answers/<int:answer_id>
    어드민 답변 삭제 API
    """

    permission_classes = [IsRoleAdminUser]
    service = AdminAnswerDeleteService()

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if request.user.is_authenticated:
            raise PermissionDenied(detail="답변 삭제 권한이 없습니다.")
        raise NotAuthenticated("로그인이 필요합니다.")

    @answer_admin_delete_schema
    def delete(self, request: Request, answer_id: int) -> Response:
        try:
            answer = self.service.delete(answer_id)
        except BaseCustomException as e:
            return Response({"error_detail": str(e)}, status=e.status_code)
        return Response(
            AdminAnswerDeleteSerializer(answer).data,
            status=status.HTTP_200_OK,
        )
