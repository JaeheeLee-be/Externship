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
    QuestionDeleteResponseSerializer,
    QuestionUpdateResponseSerializer,
    QuestionUpdateSerializer,
)
from apps.exams.services.admin_exam_question_service import (
    create_question,
    delete_question,
    get_serializer_class,
    update_question,
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
        type_serializer = get_serializer_class(request.data.get("type", "FILL_BLANK"))
        serializer = type_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data = serializer.validated_data
            new_question = create_question(exam_id, data)
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
        elif request.method == "DELETE":
            raise PermissionDenied("쪽지시험 문제 삭제 권한이 없습니다.")
        raise PermissionDenied("권한이 없습니다.")

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
            mod_question = update_question(question_id, mod_data, "update")
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
            data = delete_question(question_id, "delete")
        except ExamQuestionDeleteConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ExamQuestionDeleteNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            QuestionDeleteResponseSerializer(data).data,
            status=status.HTTP_200_OK,
        )
