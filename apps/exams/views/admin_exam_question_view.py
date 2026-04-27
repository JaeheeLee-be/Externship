from typing import Never, Optional

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.excpections.exam_question_exceptions import (
    ExamQuestionCreateConflict,
    ExamQuestionCreateNotFound,
    ExamQuestionUpdateConflict,
    ExamQuestionUpdateNotFound,
)
from apps.exams.serializers.admin_exam_question_serializer import (
    QuestionCreateResponseSerializer,
    QuestionCreateSerializer,
    QuestionUpdateResponseSerializer,
    QuestionUpdateSerializer,
)
from apps.exams.services.admin_exam_question_service import (
    QuestionService,
)


@extend_schema(
    tags=["exams_question"],
    summary="쪽지시험 문제 생성",
)
class AdminQuestionCreateView(APIView):  # TODO : ErrorDataKey 상속 추가 예정
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: Optional[str] = None, code: Optional[str] = None) -> Never:
        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("쪽지시험 문제 등록 권한이 없습니다.")

    def handle_exception(self, exc: Exception) -> Response:  # TODO : ErrorDataKey 상속 이후 변경 예정
        response: Response = super().handle_exception(exc)
        if "detail" in response.data:
            response.data["error_detail"] = response.data["detail"]
        return response

    def post(self, request: Request, exam_id: int) -> Response:
        serializer = QuestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 문제 등록 데이터입니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():
                data = serializer.validated_data
                service = QuestionService(exam_id)
                new_question = service.create_question(data)
        except ExamQuestionCreateConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ExamQuestionCreateNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(QuestionCreateResponseSerializer(new_question).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["exams_question"],
    summary="쪽지시험 문제 수정",
)
class AdminQuestionUpdateView(APIView):  # TODO : ErrorDataKey 상속 추가 예정
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: Optional[str] = None, code: Optional[str] = None) -> Never:
        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("쪽지시험 문제 수정 권한이 없습니다.")

    def handle_exception(self, exc: Exception) -> Response:  # TODO : ErrorDataKey 상속 이후 변경 예정
        if hasattr(exc, "detail") and hasattr(exc, "status_code"):
            return Response({"error_detail": exc.detail}, status=exc.status_code)
        return super().handle_exception(exc)

    def put(self, request: Request, exam_id: int, question_id: int) -> Response:
        serializer = QuestionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 문제 수정 데이터 입니다"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():
                mod_data = serializer.validated_data
                service = QuestionService(exam_id)
                mod_question = service.update_question(mod_data, question_id)
        except ExamQuestionUpdateConflict as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ExamQuestionUpdateNotFound as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(QuestionUpdateResponseSerializer(mod_question).data, status=status.HTTP_200_OK)
