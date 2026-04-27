from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser

# TODO : 예외 폴더 생성 후 경로 변경
from apps.exams.exceptions.exam_deploy_exceptions import (
    DeploymentConflictError,
    DeploymentNoQuestionsError,
    DeploymentNotFoundError,
)
from apps.exams.serializers.admin_exam_deployment_serializer import (
    AdminExamDeploymentCreateSerializer,
)
from apps.exams.services.admin_exam_deployment_service import (
    create_deployment,
)


class AdminExamDeploymentCreateView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> None:
        if request.user and request.user.is_authenticated:
            raise PermissionDenied({"error_detail": "쪽지시험 배포 생성 권한이 없습니다."})
        raise NotAuthenticated({"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})

    def post(self, request: Request) -> Response:
        serializer = AdminExamDeploymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": "유효하지 않은 배포 생성 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        # TODO : 핸들러 적용 후 try/except 제거
        try:
            deployment = create_deployment(serializer.validated_data)
        except DeploymentNoQuestionsError:
            return Response({"error_detail": "유효하지 않은 배포 생성 요청입니다."}, status=status.HTTP_400_BAD_REQUEST)
        except DeploymentNotFoundError:
            return Response(
                {"error_detail": "배포 대상 과정-기수 또는 시험 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DeploymentConflictError:
            return Response({"error_detail": "동일한 조건의 배포가 이미 존재합니다."}, status=status.HTTP_409_CONFLICT)
        return Response({"pk": deployment.id}, status=status.HTTP_201_CREATED)
