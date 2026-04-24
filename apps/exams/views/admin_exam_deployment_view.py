from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exams.serializers.admin_exam_deployment_serializer import (
    ExamDeploymentCreateSerializer,
)
from apps.exams.services.admin_exam_deployment_service import (
    DeploymentConflictError,
    create_deployment,
)


class AdminExamDeploymentCreateView(APIView):
    # TODO : user 팀 퍼미션 완성 후 교체
    permission_classes = []

    def post(self, request: Request) -> Response:
        serializer = ExamDeploymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": "유효하지 않은 배포 생성 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            deployment = create_deployment(serializer.validated_data)
        except NotFound:
            return Response(
                {"error_detail": "배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DeploymentConflictError:
            return Response({"error_detail": "동일한 조건의 배포가 이미 존재합니다."}, status=status.HTTP_409_CONFLICT)
        except ValidationError:
            return Response({"error_detail": "유효하지 않은 배포 생성 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "배포가 생성되었습니다.", "id": deployment.id}, status=status.HTTP_201_CREATED)
