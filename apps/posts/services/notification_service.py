from typing import Any

from apps.posts.models.comment import PostComment
from apps.posts.models.notification import Notification
from apps.posts.models.post import Post
from apps.users.models import User


def create_notification(
    sender: User, post: Post, comment: PostComment, parent_comment: PostComment | None = None
) -> None:
    recipients = set()

    if parent_comment is not None:
        if parent_comment.author_id != sender.id:
            recipients.add(parent_comment.author_id)
    else:
        if post.author_id != sender.id:
            recipients.add(post.author_id)

        commenter_ids = (
            PostComment.objects.filter(post=post, parent__isnull=True)
            .exclude(author=sender)
            .exclude(author_id=post.author_id)
            .values_list("author_id", flat=True)
            .distinct()
        )
        recipients.update(commenter_ids)

    Notification.objects.bulk_create(
        [
            Notification(
                recipient_id=recipient_id,
                sender=sender,
                post=post,
                comment=comment,
            )
            for recipient_id in recipients
        ]
    )


def get_notifications(user: User) -> dict[str, Any]:
    qs = Notification.objects.filter(recipient=user).select_related("sender", "post", "comment")
    return {
        "unread_count": qs.filter(is_read=False).count(),
        "notifications": qs,
    }


def mark_notifications_read(user: User) -> None:
    Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
