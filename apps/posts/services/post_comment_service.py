from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from apps.posts.exceptions import (
    CommentNotFoundError,
    CommentPermissionDeniedError,
    PostNotFoundError,
)
from apps.posts.models.comment import PostComment, PostCommentTag
from apps.posts.models.post import Post
from apps.users.models import User


def get_comments(post_id: int, page: int, page_size: int, base_url: str) -> dict[str, Any]:
    if not Post.objects.filter(id=post_id).exists():
        raise PostNotFoundError("해당 게시글을 찾을 수 없습니다.")

    page = max(page, 1)
    page_size = max(page_size, 1)
    offset = (page - 1) * page_size

    qs = PostComment.objects.filter(post_id=post_id).select_related("author").prefetch_related("tags__tagged_user")

    total_count = qs.count()
    comments = qs[offset : offset + page_size]

    next_page = f"{base_url}?page={page + 1}&page_size={page_size}" if (page * page_size) < total_count else None
    previous_page = f"{base_url}?page={page - 1}&page_size={page_size}" if page > 1 else None

    return {
        "count": total_count,
        "next": next_page,
        "previous": previous_page,
        "results": comments,
    }


@transaction.atomic
def create_comment(user: User, post_id: int, content: str, tagged_user_ids: list[int]) -> PostComment:
    if not Post.objects.filter(id=post_id).exists():
        raise PostNotFoundError("해당 게시글을 찾을 수 없습니다.")

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
