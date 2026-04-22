from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel

from .question_models import Question


class Answer(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=False)
    content = models.TextField(null=False)
    is_adopted = models.BooleanField(default=False)

    class Meta:
        db_table = "answer"


class AnswerImage(TimeStampModel):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=False)
    img_url = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "answer_image"


class AnswerComment(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=False)
    content = models.TextField(null=False)

    class Meta:
        db_table = "answer_comment"
