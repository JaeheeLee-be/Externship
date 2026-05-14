from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel
from apps.posts.models.comment import PostComment
from apps.posts.models.post import Post


class Notification(TimeStampModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="notifications")
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name="notifications")
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
