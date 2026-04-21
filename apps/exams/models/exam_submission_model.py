from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import TimeStampModel

from .exam_deployment_model import ExamDeployment


class ExamSubmission(TimeStampModel):
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    deployment = models.ForeignKey(ExamDeployment, on_delete=models.CASCADE)
    started_at = models.DateTimeField()
    cheating_count = models.SmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(3)],
        default=0,
    )
    answer_json = models.JSONField(default=dict)
    score = models.SmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
    )
    correct_answer_count = models.SmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        default=0,
    )

    class Meta:
        db_table = "exam_submissions"
