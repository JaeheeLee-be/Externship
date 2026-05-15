from typing import Any, Optional

from django.db.models import Count, Q, QuerySet

from apps.posts.exceptions import PostNotFoundError, PostPermissionDeniedError
from apps.posts.models import Post
from apps.users.models import User

SORT_MAP = {
    "latest": "-created_at",
    "oldest": "created_at",
    "most_views": "-view_count",
    "most_likes": "-like_count",
    "most_comments": "-comment_count",
}

DEFAULT_SORT = "-created_at"


def list_posts(
    search: Optional[str] = None,
    search_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    sort: str = "latest",
) -> QuerySet[Post]:
    queryset = Post.objects.annotate(
        like_count=Count("likes", filter=Q(likes__is_liked=True), distinct=True),
        comment_count=Count("comments", distinct=True),
    ).select_related("author", "category")

    if category_id:
        queryset = queryset.filter(category_id=category_id)

    if search and search_filter:
        if search_filter == "author":
            queryset = queryset.filter(author__nickname__icontains=search)
        elif search_filter == "title":
            queryset = queryset.filter(title__icontains=search)
        elif search_filter == "content":
            queryset = queryset.filter(content__icontains=search)
        elif search_filter == "title_or_content":
            queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))

    return queryset.order_by(SORT_MAP.get(sort, DEFAULT_SORT))


def create_post(author: User, validated_data: dict[str, Any]) -> Post:
    return Post.objects.create(author=author, **validated_data)


def get_post(post_id: int) -> Post:
    try:
        return Post.objects.annotate(
            like_count=Count("likes", filter=Q(likes__is_liked=True), distinct=True),
        ).get(pk=post_id)
    except Post.DoesNotExist:
        raise PostNotFoundError("해당 게시글을 찾을 수 없습니다.")


def update_post(post_id: int, user: User, validated_data: dict[str, Any]) -> Post:
    post = get_post(post_id)
    if post.author != user:
        raise PostPermissionDeniedError("권한이 없습니다.")

    for field, value in validated_data.items():
        setattr(post, field, value)
    post.save()
    return post


def delete_post(post_id: int, user: User) -> None:
    post = get_post(post_id)
    if post.author != user:
        raise PostPermissionDeniedError("권한이 없습니다.")

    post.delete()
    return
