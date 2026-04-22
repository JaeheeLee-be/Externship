from django.db import models

from django.conf import settings


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="likes",
    )
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "post_likes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post", "is_liked"], name="idx_post_is_liked"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"],
                name="unique_user_post_like",
            )
        ]


    def __str__(self) -> str:
        status = "liked" if self.is_liked else "unliked"
        return f"{self.user_id} {status} {self.post_id}"
