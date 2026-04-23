from typing import Any, Dict

from django.db import transaction
from django.db.models import QuerySet, Sum
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion

question_type_list = ["fill_blank", "ordering", "multiple_choice", "single_choice", "short_answer", "ox"]


class ServiceException(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        self.message = message
        self.status_code = status_code


class CustomPermissions(IsAuthenticated):
    message = "쪽지시험 문제 등록 권한이 없습니다."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "PUT":
            self.message = "쪽지시험 문제 수정 권한이 없습니다."
        elif request.method == "DELETE":
            self.message = "쪽지시험 문제 삭제 권한이 없습니다."
        if not super().has_permission(request, view):
            self.message = "자격 인증 데이터가 제공되지 않았습니다."
            return False
        if getattr(request.user, "role", None) == "USER":
            return False
        return True


class QuestionService:

    @staticmethod
    def get_queryset(exam_id: int, question_id: int) -> QuerySet[ExamQuestion]:
        exam = Exam.objects.filter(pk=exam_id).exists()
        if not exam:
            raise ServiceException("해당 쪽지시험 정보를 찾을 수 없습니다.", status_code=status.HTTP_404_NOT_FOUND)
        question = ExamQuestion.objects.filter(exam_id=exam_id, id=question_id)
        if not question:
            raise ServiceException("해당 쪽지시험 문제 정보를 찾을 수 없습니다.", status_code=status.HTTP_404_NOT_FOUND)
        return question

    @staticmethod
    @transaction.atomic  # 과정에서의 한번의 실패가 전체 실패로 적용 (원자성)
    def create_question(exam_id: int, data: Dict[str, Any]) -> ExamQuestion:
        # DB lock
        # select_for_update을 사용함으로써 해당 exam객체에 대한 수정이나 삭제가 불가능함 (무결성)
        exam = Exam.objects.select_for_update().filter(pk=exam_id).first()
        if not exam:
            raise ServiceException("해당 쪽지시험 정보를 찾을 수 없습니다.", status_code=status.HTTP_404_NOT_FOUND)
        # 총 문제 갯수 제한
        if exam.examquestion_set.count() >= 20:
            raise ServiceException(
                "해당 쪽지시험에 등록 가능한 문제 수 또는 총 배점을 초과했습니다", status_code=status.HTTP_409_CONFLICT
            )
        # 총 배점 제한
        result = ExamQuestion.objects.filter(exam_id=exam_id).aggregate(total=Sum("point"))
        total_points = result.get("total") or 0
        new_point = data.get("point") or 0
        if new_point + total_points > 100:
            raise ServiceException(
                "해당 쪽지시험에 등록 가능한 문제 수 또는 총 배점을 초과했습니다", status_code=status.HTTP_409_CONFLICT
            )
        # 문제 유형 존재 여부 검사
        question_type = data.get("type")
        if question_type not in question_type_list:
            raise ServiceException("유효하지 않은 문제 등록 데이터입니다.", status_code=status.HTTP_400_BAD_REQUEST)
        new_question = ExamQuestion.objects.create(exam_id=exam_id, **data)
        return new_question

    @staticmethod
    @transaction.atomic
    def update_question(exam_id: int, question_id: int, serializer_data: Dict[str, Any]) -> ExamQuestion:
        question = ExamQuestion.objects.select_for_update().filter(exam_id=exam_id, id=question_id).first()
        if not question:
            raise ServiceException("수정하려는 문제 정보를 찾을 수 없습니다.", status_code=status.HTTP_404_NOT_FOUND)
            # 수정 데이터의 배점 검증
        mod_point = serializer_data.get("point", 1)
        result = ExamQuestion.objects.filter(exam_id=exam_id).aggregate(total=Sum("point"))
        total_points = result.get("total") or 0
        if mod_point + total_points - question.point > 100:
            raise ServiceException(
                "해당 쪽지시험에 등록 가능한 문제 수 또는 총 배점을 초과하여 문제를 수정할 수 없습니다.",
                status_code=status.HTTP_409_CONFLICT,
            )
            # 수정 데이터의 문제 유형 검증
        mod_type = serializer_data.get("type", question.type)
        if mod_type not in question_type_list:
            raise ServiceException("유효하지 않은 문제 수정 데이터입니다.", status_code=status.HTTP_400_BAD_REQUEST)
            # question.update(serializer.data)는 사용 불가능 각 데이터들을 key와 value로 나눠서 풀어줘야함
        for k, v in serializer_data.items():
            setattr(question, k, v)
        question.save()
        return question
