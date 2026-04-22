from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel
from apps.posts.models.category import PostCategory


class Post(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    category = models.ForeignKey(PostCategory, on_delete=models.PROTECT, related_name="posts")
    title = models.CharField(max_length=50)
    content = models.TextField()
    view_count = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    is_notice = models.BooleanField(default=False)

    class Meta:
        db_table = "post"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
