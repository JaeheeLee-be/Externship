from django.db import models

from apps.core.models import TimeStampModel
from apps.posts.models import Subject


class Exam(TimeStampModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="exams")
    title = models.CharField(max_length=50, unique=True)
    thumbnail_img_url = models.CharField(max_length=255, default="default_img_url")

    class Meta:
        db_table = "exams"
        ordering = ["-created_at", "title"]

    def __str__(self) -> str:
        return self.title
