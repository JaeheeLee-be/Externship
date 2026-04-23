from django.db import models

from apps.core.models import TimeStampModel

from .course import Course


class StatusChoices(models.TextChoices):
    SUBMITTED = "SUBMITTED", "대기"
    ACCEPTED = "ACCEPTED", "승인"
    REJECTED = "REJECTED", "거절"


class Cohort(TimeStampModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="cohorts")
    number = models.PositiveSmallIntegerField()
    max_student = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.SUBMITTED)

    class Meta:
        db_table = "cohorts"
        unique_together = (("course", "number"),)
