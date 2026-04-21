from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampModel

from .exam_model import Exam


class ExamQuestion(TimeStampModel):

    class QuestionType(models.TextChoices):
        BLANK = "blank", "빈칸채우기"
        SORT = "sort", "순서정렬"
        CHOICE = "choice", "다지선다"
        SENTENCE = "sentence", "주관식"
        WORD = "word", "단답형"
        QUIZ = "quiz", "OX퀴즈"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    prompt = models.TextField(null=True, blank=True)
    blank_count = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)], null=True, blank=True
    )
    optional_json = models.TextField(null=True, blank=True)
    type = models.CharField(choices=QuestionType.choices, max_length=10)
    answer = models.JSONField(
        default=dict,
    )
    point = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    explanation = models.TextField(default="")

    class Meta:
        db_table = "exam_questions"
