from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exams.serializers.admin_exam_deployment_serializer import (
    ExamDeploymentCreateSerializer,
)
from apps.exams.services.admin_exam_deployment_service import create_deployment


class AdminExamDeploymentCreateView(APIView):
    # TODO : user 팀 퍼미션 완성 후 교체
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = ExamDeploymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deployment = create_deployment(serializer.validated_data)
        return Response({"message": "배포가 생성되었습니다.", "id": deployment.id}, status=status.HTTP_201_CREATED)
