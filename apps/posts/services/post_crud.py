from typing import Any

from apps.posts.exceptions import PostNotFoundError, PostPermissionDeniedError
from apps.posts.models import Post
from apps.users.models import User


def list_posts() -> list[Post]:
    return list(Post.objects.all())


def create_post(author: User, validated_data: dict[str, Any]) -> Post:
    return Post.objects.create(author=author, **validated_data)


def get_post(post_id: int) -> Post:
    try:
        return Post.objects.get(pk=post_id)
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