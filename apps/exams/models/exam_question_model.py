from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampModel

from .exam_model import Exam


class ExamQuestion(TimeStampModel):

    class QuestionType(models.TextChoices):
        FILL_BLANK = "fill_blank", "빈칸채우기"
        ORDERING = "ordering", "순서정렬"
        MULTIPLE_CHOICE = "multiple_choice","다지선다(복수선택)"
        SINGLE_CHOICE = "single_choice", "다지선다(단일선택)"
        SHORT_ANSWER = "short_answer", "단답형"
        OX = "ox", "OX퀴즈"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.CharField(max_length=255)
    prompt = models.TextField(null=True, blank=True)
    blank_count = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)], null=True, blank=True
    )
    optional_json = models.TextField(null=True, blank=True)
    type = models.CharField(choices=QuestionType.choices, max_length=20)
    answer = models.JSONField(
        default=dict,
    )
    point = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    explanation = models.TextField(default="")

    class Meta:
        db_table = "exam_questions"
