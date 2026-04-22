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


class QuestionCreateView(APIView):
    permission_classes = [CustomPermissions]

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
                print(f"DEBUG - Serializer Errors: {serializer.errors}")  # 이 줄을 추
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": e.message}, status=e.status_code)
        # 응답할때는 전체를 다 보여주기
        return Response(QuestionSerializer(result).data, status=status.HTTP_201_CREATED)


class QuestionDetailView(APIView):
    permission_classes = [CustomPermissions]

    # 수정
    def put(self, request:Request, exam_id:int, question_id:int)->Response:
        mod_data = request.data
        serializer_class = SERIALIZER_MAP.get(str(mod_data.get("type","")), QuestionSerializer)
        serializer = serializer_class(data=mod_data)
        try:
            serializer.is_valid(raise_exception=True)
            mod_question = QuestionService.update_question(exam_id, question_id, serializer.validated_data)
        except (ServiceException, ValidationError) as e:
            if isinstance(e, ValidationError):
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": e.message, "status": e.status_code})
        return Response(QuestionSerializer(mod_question).data, status=status.HTTP_200_OK)
