from django.conf import settings
from django.db import models


class QuestionCategories(models.Model):
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
    name = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_categories"


class Questions(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(QuestionCategories, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.TextField()
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"


class QuestionImages(models.Model):
    question = models.ForeignKey(Questions, on_delete=models.CASCADE)
    img_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "question_images"
