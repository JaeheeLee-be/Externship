from django.db import models
from .course import Course
from apps.core.models import TimeStampModel

class StatusChoices(models.TextChoices):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'

class Cohort(TimeStampModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='cohorts')
    number = models.PositiveSmallIntegerField()
    max_student = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )

    class Meta:
        db_table = 'cohorts'
        unique_together = (('course', 'number'),)