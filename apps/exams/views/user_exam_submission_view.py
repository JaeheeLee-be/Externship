from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsStudentUser
from apps.exams.exceptions.exam_submission_exception import UserSubmissionNotFound
from apps.exams.serializers.user_exam_submission_serializer import (
    UserExamSubmissionExtendSchemaSerializer,
    UserExamSubmissionGetSerializer,
)
from apps.exams.services.user_exam_submission_service import get_submission_detail


class UserExamSubmissionGetView(APIView):

    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["user-exams-submission"],
        summary="쪽지시험 결과 확인 API",
        responses={
            200: UserExamSubmissionExtendSchemaSerializer,
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
            404: OpenApiResponse(description="해당 시험 정보를 찾을 수 없습니다."),
        },
    )
    def get(self, request: Request, submission_id: int) -> Response:
        try:
            assert request.user.id is not None
            submission = get_submission_detail(submitter=request.user.id, submission_id=submission_id)
        except UserSubmissionNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserExamSubmissionGetSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)
