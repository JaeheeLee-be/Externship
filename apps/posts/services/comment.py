from django.db.models import QuerySet

from apps.posts.exceptions import CommentNotFoundError, CommentPermissionDeniedError
from apps.posts.models.comment import PostComment, PostCommentTag
from apps.users.models import User


def get_comments(post_id: int, page: int, page_size: int) -> tuple[int, QuerySet["PostComment"]]:
    offset = (page - 1) * page_size

    qs = PostComment.objects.filter(post_id=post_id).select_related("author").prefetch_related("tags__tagged_user")

    total_count = qs.count()
    comments = qs[offset : offset + page_size]

    return total_count, comments


def create_comment(user: User, post_id: int, content: str, tagged_user_ids: list[int]) -> PostComment:
    comment = PostComment.objects.create(author=user, post_id=post_id, content=content)

    if tagged_user_ids:
        PostCommentTag.objects.bulk_create(
            [PostCommentTag(comment=comment, tagged_user_id=uid) for uid in tagged_user_ids], ignore_conflicts=True
        )
    return PostComment.objects.select_related("author").prefetch_related("tags__tagged_user").get(id=comment.id)


def delete_comment(user: User, comment_id: int, post_id: int) -> None:
    try:
        comment = PostComment.objects.get(id=comment_id, post_id=post_id)
    except PostComment.DoesNotExist:
        raise CommentNotFoundError("해당 댓글을 찾을 수 없습니다.")

    if comment.author_id != user.id:
        raise CommentPermissionDeniedError("권한이 없습니다.")

    comment.delete()
