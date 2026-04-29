import json
from typing import Any, Dict, Literal

from django.db import transaction

from apps.exams.exceptions.exam_question_exceptions import (
    ExamQuestionCreateConflict,
    ExamQuestionCreateNotFound,
    ExamQuestionDeleteNotFound,
    ExamQuestionUpdateConflict,
    ExamQuestionUpdateNotFound,
)
from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion


class AdminQuestionService:

    def __init__(self, exam_id: int, method: Literal["create", "update", "delete"]):
        self.exam_id = exam_id
        self.method = method
        self.atomic = transaction.atomic()

    def __enter__(self) -> "AdminQuestionService":
        self.atomic.__enter__()
        exam = Exam.objects.prefetch_related("examquestion_set").select_for_update().filter(id=self.exam_id).first()
        if not exam:
            self.atomic.__exit__(None, None, None)
            if self.method == "create":
                raise ExamQuestionCreateNotFound()
            elif self.method == "update":
                raise ExamQuestionUpdateNotFound()
            elif self.method == "delete":
                raise ExamQuestionDeleteNotFound()
        self.exam = exam
        self.questions = list(self.exam.examquestion_set.all())
        self.len_of_questions = len(self.questions)
        self.total_point = sum(question.point for question in self.questions)
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
        self.questions.append(new_question)
        return new_question

    def update_question(self, data: Dict[str, Any], question_id: int) -> ExamQuestion:
        if "options_json" in data:
            data["options_json"] = json.dumps(data["options_json"])
        target_question = next((question for question in self.questions if question.id == question_id), None)
        if not target_question:
            raise ExamQuestionUpdateNotFound()
        if self.total_point + data.get("point", target_question.point) - target_question.point > 100:
            raise ExamQuestionUpdateConflict()
        for k, v in data.items():
            setattr(target_question, k, v)
        target_question.save(update_fields=list(data.keys()))
        return target_question

    def delete_question(self, question_id: int) -> ExamQuestion:
        target_question = next((question for question in self.questions if question.id == question_id), None)
        if not target_question:
            raise ExamQuestionDeleteNotFound()
        target_question.delete()
        self.questions.remove(target_question)
        return target_question
