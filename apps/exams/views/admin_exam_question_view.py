from typing import NoReturn, Optional

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.exceptions.exam_question_exceptions import (
    ExamQuestionCreateConflict,
    ExamQuestionCreateNotFound,
    ExamQuestionDeleteConflict,
    ExamQuestionDeleteNotFound,
    ExamQuestionUpdateConflict,
    ExamQuestionUpdateNotFound,
)
from apps.exams.serializers.admin_exam_question_serializer import (
    QuestionCreateResponseSerializer,
    QuestionCreateSerializer,
    QuestionDeleteResponseSerializer,
    QuestionUpdateResponseSerializer,
    QuestionUpdateSerializer,
)
from apps.exams.services.admin_exam_question_service import (
    AdminQuestionService,
)


@extend_schema(
    tags=["exams_question"],
    summary="쪽지시험 문제 생성",
)
class AdminQuestionCreateView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(
        self, request: Request, message: Optional[str] = None, code: Optional[str] = None
    ) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("쪽지시험 문제 등록 권한이 없습니다.")

    def post(self, request: Request, exam_id: int) -> Response:
        serializer = QuestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            with AdminQuestionService(method="create", exam_id=exam_id) as service:
                new_question = service.create_question(data)
        except ExamQuestionCreateConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ExamQuestionCreateNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(QuestionCreateResponseSerializer(new_question).data, status=status.HTTP_201_CREATED)


class AdminQuestionUpdateDeleteView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(
        self, request: Request, message: Optional[str] = None, code: Optional[str] = None
    ) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        if request.method == "PUT":
            raise PermissionDenied("쪽지시험 문제 수정 권한이 없습니다.")
        raise PermissionDenied("쪽지시험 문제 삭제 권한이 없습니다.")

    @extend_schema(
        tags=["exams_question"],
        summary="쪽지시험 문제 수정",
    )
    def put(self, request: Request, question_id: int) -> Response:
        serializer = QuestionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            mod_data = serializer.validated_data
            with AdminQuestionService(method="update", question_id=question_id) as service:
                mod_question = service.update_question(mod_data)
        except ExamQuestionUpdateConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ExamQuestionUpdateNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(QuestionUpdateResponseSerializer(mod_question).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["exams_question"],
        summary="쪽지시험 문제 삭제",
    )
    def delete(self, request: Request, question_id: int) -> Response:
        try:
            with AdminQuestionService(method="delete", question_id=question_id) as service:
                question_id, exam_id = service.delete_question()
        except ExamQuestionDeleteConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ExamQuestionDeleteNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            QuestionDeleteResponseSerializer({"question_id": question_id, "exam_id": exam_id}).data,
            status=status.HTTP_200_OK,
        )
