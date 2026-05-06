import json
from typing import Any, Dict, Literal, Tuple

from django.db import transaction
from django.db.models import Count, Sum

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


# TODO : 함수형으로 리펙토링 예정
class AdminQuestionService:
    exam: Exam
    target_question: ExamQuestion
    total_point: int
    len_of_questions: int

    def __init__(
        self, method: Literal["create", "update", "delete"], exam_id: int | None = None, question_id: int | None = None
    ):
        self.exam_id = exam_id
        self.question_id = question_id
        self.method = method
        self.atomic = transaction.atomic()

    def __enter__(self) -> "AdminQuestionService":

        self.atomic.__enter__()

        if self.method == "create":
            assert self.exam_id is not None
            exam = Exam.objects.select_for_update().filter(id=self.exam_id).first()
            result = ExamQuestion.objects.filter(exam=exam).aggregate(
                total_point=Sum("point"), len_of_questions=Count("id")
            )

        else:
            assert self.question_id is not None
            target_question = ExamQuestion.objects.filter(id=self.question_id).first()
            if not target_question:
                self.atomic.__exit__(None, None, None)
                if self.method == "update":
                    raise ExamQuestionUpdateNotFound()
                else:
                    raise ExamQuestionDeleteNotFound()

            self.target_question = target_question

            if self.method == "update":

                exam = Exam.objects.select_for_update().filter(id=target_question.exam_id).first()
                result = ExamQuestion.objects.filter(exam=exam).aggregate(
                    total_point=Sum("point"),
                )
            else:
                exam = Exam.objects.select_for_update().filter(id=target_question.exam_id).first()
                result = ExamQuestion.objects.filter(exam=exam).aggregate(len_of_questions=Count("id"))

        if not exam:
            self.atomic.__exit__(None, None, None)
            if self.method == "create":
                raise ExamQuestionCreateNotFound()
            elif self.method == "update":
                raise ExamQuestionUpdateNotFound()

        assert exam is not None
        self.exam = exam
        self.len_of_questions = result.get("len_of_questions") or 0
        self.total_point = result.get("total_point") or 0
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Any) -> None:
        self.atomic.__exit__(exc_type, exc_value, traceback)

    def create_question(self, data: Dict[str, Any]) -> ExamQuestion:
        if "options_json" in data:
            data["options_json"] = json.dumps(data["options_json"])
        if self.len_of_questions >= 20:
            raise ExamQuestionCreateConflict()
        if self.total_point + data["point"] > 100:
            raise ExamQuestionCreateConflict()
        new_question = ExamQuestion.objects.create(exam=self.exam, **data)
        return new_question

    def update_question(self, data: Dict[str, Any]) -> ExamQuestion:
        if "options_json" in data:
            data["options_json"] = json.dumps(data["options_json"])
        if self.total_point + data.get("point", self.target_question.point) - self.target_question.point > 100:
            raise ExamQuestionUpdateConflict()
        for k, v in data.items():
            setattr(self.target_question, k, v)
        self.target_question.save(update_fields=list(data.keys()))
        return self.target_question

    def delete_question(self) -> Tuple[int, int]:
        if self.len_of_questions == 1:
            raise ExamQuestionDeleteConflict()
        self.target_question.delete()
        question_id = self.target_question.id
        exam_id = self.exam.id
        return question_id, exam_id
