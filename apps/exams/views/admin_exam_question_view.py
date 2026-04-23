from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.exams.serializers.admin_exam_question_serializer import (
    BlankSerializer,
    ChoiceAndSortSerializer,
    QuestionSerializer,
    WordAndQuizSerializer,
)
from apps.exams.services.admin_exam_question_service import (
    CustomPermissions,
    QuestionService,
    ServiceException,
)

# 문제유형별 시리얼라이저
SERIALIZER_MAP = {
    "FILL_BLANK": BlankSerializer,
    "OX": WordAndQuizSerializer,
    "SHORT_ANSWER": WordAndQuizSerializer,
    "SINGLE_CHOICE": ChoiceAndSortSerializer,
    "MULTIPLE_CHOICE": ChoiceAndSortSerializer,
    "ORDERING": ChoiceAndSortSerializer,
}

@extend_schema(
    tags=["exams_question"],
    summary="쪽지시험 문제 생성",
    description="""
        쪽지시험 문제를 생성,
         각 문제 유형별 serializer 적용하여 필수 데이터만 입력,
         하나의 쪽지시험에는 최대 20개의 문제등록가능,
        문제들의 배점의 합은 100점
    """
)
class QuestionCreateView(APIView):
    permission_classes = [CustomPermissions]
    serializer_class = QuestionSerializer

    # 생성
    def post(self, request: Request, exam_id: int) -> Response:
        question_type = request.data.get("type", "")
        # 객체 생성 로직에서는 타입별 시리얼라이저를 사용하여 객체생성
        serializer_class = SERIALIZER_MAP.get(question_type, QuestionSerializer)
        serializer = serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            result = QuestionService.create_question(exam_id, serializer.validated_data)
        except (ServiceException, ValidationError) as e:
            if isinstance(e, ValidationError):
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": e.message}, status=e.status_code)
        # 응답할때는 전체를 다 보여주기
        return Response(QuestionSerializer(result).data, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=["exams_question"],
    summary="쪽지시험 문제 단일 삭제 및 수정",
    description="""
        쪽지시험 문제 삭제 및 수정,
        수정후 총 배점 100점 검증 포함
    """
)
class QuestionDetailView(APIView):
    permission_classes = [CustomPermissions]

    # 수정
    def put(self, request: Request, exam_id: int, question_id: int) -> Response:
        mod_data = request.data
        serializer_class = SERIALIZER_MAP.get(str(mod_data.get("type", "")), QuestionSerializer)
        serializer = serializer_class(data=mod_data)
        try:
            serializer.is_valid(raise_exception=True)
            mod_question = QuestionService.update_question(exam_id, question_id, serializer.validated_data)
        except (ServiceException, ValidationError) as e:
            if isinstance(e, ValidationError):
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": e.message, "status": e.status_code})
        return Response(QuestionSerializer(mod_question).data, status=status.HTTP_200_OK)
