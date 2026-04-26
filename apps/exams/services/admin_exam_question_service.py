from typing import Any, Dict

from apps.exams.excpections.exam_question_exceptions import (
    ExamQuestionConflict,
    ExamQuestionNotFound,
)
from apps.exams.models.exam_model import Exam
from apps.exams.models.exam_question_model import ExamQuestion


class QuestionService:

    def __init__(self, exam_id: int):
        self.exam = Exam.objects.prefetch_related("examquestion_set").select_for_update().filter(id=exam_id).first()
        if not self.exam:
            raise ExamQuestionNotFound()
        self.questions = list(self.exam.examquestion_set.all())

    @property
    def len_of_questions(self):
        return len(self.questions)

    @property
    def total_point(self):
        return sum(question.point for question in self.questions)

    def create_question(self, data: Dict[str, Any]) -> ExamQuestion:
        if self.len_of_questions >= 20:
            raise ExamQuestionConflict()
        if self.total_point + data["point"] > 100:
            raise ExamQuestionConflict()
        question = ExamQuestion.objects.create(exam=self.exam, **data)
        self.questions.append(question)
        return question

    def update_question(self, data: Dict[str, Any], question_id: int) -> ExamQuestion:
        target_question = next((question for question in self.questions if question.id == question_id), None)
        if not target_question:
            raise ExamQuestionNotFound()
        if "point" in data:
            if self.total_point + data["point"] - target_question.point > 100:
                raise ExamQuestionConflict()
        for k, v in data.items():
            setattr(target_question, k, v)
        target_question.save()
        return target_question
