from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel


class QuestionCategory(TimeStampModel):
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=15, null=False)

    class Meta:
        db_table = "question_categories"


class Question(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False)
    category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=50, null=False)
    content = models.TextField(null=False)
    view_count = models.BigIntegerField(default=0, null=False)

    class Meta:
        db_table = "questions"


class QuestionImage(TimeStampModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=False)
    img_url = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "question_images"
