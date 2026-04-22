from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel


class PostComment(TimeStampModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=500)

    class Meta:
        db_table = "post_comment"
        ordering = ["id"]


class PostCommentTag(TimeStampModel):
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name="tags")
    tagged_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tagged_in_comments"
    )

    class Meta:
        db_table = "post_comment_tags"
