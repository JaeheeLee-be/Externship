from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.core.utils.permissions import IsRoleAdminUser
from apps.qna.services.admin_answer_service import AdminAnswerDeleteService

from apps.qna.serializers.admin_answer_serializers import AdminAnswerDeleteSerializer
from rest_framework import status
class AdminAnswerDeleteView(APIView):
    """
    DELETE api/v1/admin/answers/<int:answer_id>
    어드민 답변 삭제 API
    """
    permission_classes = [IsAuthenticated,IsRoleAdminUser]
    service = AdminAnswerDeleteService()

    def delete(self,request:Request,answer_id:int)->Response:
        answer = self.service.delete(answer_id)
        return Response(
            AdminAnswerDeleteSerializer(answer).data,
            status=status.HTTP_200_OK,
        )