import json
from typing import Any, Dict, Tuple

from django.db import transaction
from django.db.models import Count, Sum
from rest_framework import serializers

from apps.exams.exceptions.exam_question_exceptions import (
    ExamQuestionCreateConflict,
    ExamQuestionCreateNotFound,
    ExamQuestionDeleteConflict,
    ExamQuestionDeleteNotFound,
    ExamQuestionUpdateConflict,
    ExamQuestionUpdateNotFound,
)
from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion
from apps.exams.serializers.admin_exam_question_serializer import (
    BlankRequestSerializer,
    MulAndSingleRequestSerializer,
    OrderRequestSerializer,
    OXAndShortRequestSerializer,
)

SERIALIZER_MAP = {
    "fill_blank": BlankRequestSerializer,
    "ordering": OrderRequestSerializer,
    "multiple_choice": MulAndSingleRequestSerializer,
    "single_choice": MulAndSingleRequestSerializer,
    "short_answer": OXAndShortRequestSerializer,
    "ox": OXAndShortRequestSerializer,
}

ALLOWED_UPDATE_FIELD = ["type", "answer", "question", "prompt", "blank_count", "options_json", "point", "explanation"]


def get_serializer_class(question_type: str) -> type[serializers.ModelSerializer[Any]]:
    serializer = SERIALIZER_MAP.get(question_type, BlankRequestSerializer)
    return serializer


def _get_exam_lock_with_data(exam_id: int) -> Tuple[int, int, Exam]:
    exam = Exam.objects.filter(id=exam_id).select_for_update().first()
    if not exam:
        raise ExamQuestionCreateNotFound()

    result = ExamQuestion.objects.filter(exam_id=exam.id).aggregate(
        total_point=Sum("point"), len_of_question=Count("id")
    )

    total_point = result.get("total_point") or 0
    len_of_question = result.get("len_of_question") or 0

    return total_point, len_of_question, exam


def _get_question(question_id: int, method: str) -> ExamQuestion:

    target_question = ExamQuestion.objects.filter(id=question_id).select_for_update().first()
    if not target_question:
        if method == "update":
            raise ExamQuestionUpdateNotFound()
        elif method == "delete":
            raise ExamQuestionDeleteNotFound()
        else:
            raise ExamQuestionCreateNotFound("찾을수 없습니다.")

    return target_question


def _get_exam_with_total_point(exam_id: int) -> Tuple[int, Exam]:

    exam = Exam.objects.filter(id=exam_id).select_for_update().first()
    if not exam:
        raise ExamQuestionUpdateNotFound()

    result = ExamQuestion.objects.filter(exam_id=exam.id).aggregate(total_point=Sum("point"))

    total_point = result.get("total_point") or 0

    return total_point, exam


def _get_exam_lock_with_len(exam_id: int) -> int:

    exam = Exam.objects.filter(id=exam_id).select_for_update().first()
    if not exam:
        raise ExamQuestionDeleteNotFound()

    result = ExamQuestion.objects.filter(exam_id=exam.id).aggregate(len_of_question=Count("id"))

    len_of_question = result.get("len_of_question") or 0

    return len_of_question


@transaction.atomic
def create_question(exam_id: int, data: Dict[str, Any]) -> ExamQuestion:

    total_point, len_of_question, exam = _get_exam_lock_with_data(exam_id)

    if total_point + data.get("point", 1) > 100:
        raise ExamQuestionCreateConflict()
    if len_of_question >= 20:
        raise ExamQuestionCreateConflict()

    if "options" in data:
        data["options_json"] = json.dumps(data.pop("options"))
    if "correct_answer" in data:
        data["answer"] = data.pop("correct_answer")

    new_question = ExamQuestion.objects.create(exam=exam, **data)

    return new_question


@transaction.atomic
def update_question(question_id: int, data: Dict[str, Any], method: str) -> ExamQuestion:

    target_question = _get_question(question_id, method)
    total_point, exam = _get_exam_with_total_point(target_question.exam_id)

    if total_point + data.get("point", target_question.point) - target_question.point > 100:
        raise ExamQuestionUpdateConflict()

    if "options" in data:
        data["options_json"] = json.dumps(data.pop("options"))
    if "correct_answer" in data:
        data["answer"] = data.pop("correct_answer")

    for field in ALLOWED_UPDATE_FIELD:
        if field in data:
            setattr(target_question, field, data[field])
        else:
            setattr(target_question, field, None)
    target_question.save()

    return target_question


@transaction.atomic
def delete_question(question_id: int, method: str) -> Dict[str, int]:

    target_question = _get_question(question_id, method)
    len_of_question = _get_exam_lock_with_len(target_question.exam_id)

    if len_of_question == 1:
        raise ExamQuestionDeleteConflict()
    result_id = target_question.id
    target_question.delete()

    data = {
        "exam_id": target_question.exam_id,
        "question_id": result_id,
    }

    return data
