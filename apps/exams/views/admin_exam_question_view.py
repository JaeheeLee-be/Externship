from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.excpections.exam_question_exceptions import (
    ExamQuestionForbidden,
    ExamQuestionUnauthorized,
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

    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            raise ExamQuestionUnauthorized()
        raise ExamQuestionForbidden()

    def handle_exception(self, exc):  # TODO : ErrorDataKey 상속 이후 변경 예정
        if hasattr(exc, "default_detail") and hasattr(exc, "status_code"):
            return Response({"error_detail": exc.default_detail}, status=exc.status_code)
        return super().handle_exception(exc)

    def post(self, request: Request, exam_id: int) -> Response:
        serializer = QuestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 문제 등록 데이터입니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            data = serializer.validated_data
            service = QuestionService(exam_id)
            new_question = service.create_question(data)
        return Response(QuestionCreateResponseSerializer(new_question).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["exams_question"],
    summary="쪽지시험 문제 수정",
)
class AdminQuestionUpdateView(APIView):  # TODO : ErrorDataKey 상속 추가 예정
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            raise ExamQuestionUnauthorized()
        raise ExamQuestionForbidden()

    def handle_exception(self, exc):  # TODO : ErrorDataKey 상속 이후 변경 예정
        if hasattr(exc, "default_detail") and hasattr(exc, "status_code"):
            return Response({"error_detail": exc.default_detail}, status=exc.status_code)
        return super().handle_exception(exc)

    def put(self, request: Request, exam_id: int, question_id: int) -> Response:
        serializer = QuestionUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 문제 수정 데이터 입니다"}, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            mod_data = serializer.validated_data
            service = QuestionService(exam_id)
            mod_question = service.update_question(mod_data, question_id)
        return Response(QuestionUpdateResponseSerializer(mod_question).data, status=status.HTTP_200_OK)
