from django.db import models

from apps.core.models import TimeStampModel


class PostCategory(TimeStampModel):
    name = models.CharField(max_length=20, unique=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "post_category"

    def __str__(self) -> str:
        return self.name