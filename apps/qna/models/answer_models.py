from django.conf import settings
from django.db import models

from .question_models import Questions


class Answers(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    content = models.TextField()
    is_adopted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "answers"


class AnswerImages(models.Model):
    answer = models.ForeignKey(Answers, on_delete=models.CASCADE)
    img_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "answer_images"


class AnswerComments(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answers, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "answer_comments"
