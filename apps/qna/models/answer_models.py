from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel

from .question_models import Questions


class Answers(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    question = models.ForeignKey(Questions, on_delete=models.CASCADE, null=False)
    content = models.TextField(null=False)
    is_adopted = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = "answers"


class AnswerImages(TimeStampModel):
    answer = models.ForeignKey(Answers, on_delete=models.CASCADE, null=False)
    img_url = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "answer_images"


class AnswerComments(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    answer = models.ForeignKey(Answers, on_delete=models.CASCADE, null=False)
    content = models.TextField(null=False)

    class Meta:
        db_table = "answer_comments"
