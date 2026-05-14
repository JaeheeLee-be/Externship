from apps.posts.exceptions import (
    PostAlreadyLikedError,
    PostLikeNotRegisteredError,
    PostLikePostNotFoundError,
)
from apps.posts.models import Like, Post
from apps.users.models import User


def get_visible_post_or_raise(post_id: int) -> Post:
    post = Post.objects.filter(id=post_id, is_visible=True).first()
    if post is None:
        raise PostLikePostNotFoundError("해당 게시글을 찾을 수 없습니다.")
    return post


def _get_like_count(post_id: int) -> int:
    return Like.objects.filter(post_id=post_id, is_liked=True).count()


def create_post_like(user: User, post_id: int) -> dict[str, int | bool]:
    post = get_visible_post_or_raise(post_id)
    like, created = Like.objects.get_or_create(user=user, post=post)

    if not created:
        if like.is_liked:
            raise PostAlreadyLikedError("이미 좋아요를 누른 게시글입니다.")
        like.is_liked = True
        like.save(update_fields=["is_liked", "updated_at"])

    return {"is_liked": True, "like_count": _get_like_count(post_id)}


def cancel_post_like(user: User, post_id: int) -> dict[str, int | bool]:
    post = get_visible_post_or_raise(post_id)

    like = Like.objects.filter(user=user, post=post).first()

    if like is None or not like.is_liked:
        raise PostLikeNotRegisteredError("좋아요 기록을 찾을 수 없습니다.")

    like.is_liked = False
    like.save(update_fields=["is_liked", "updated_at"])

    return {"is_liked": False, "like_count": _get_like_count(post_id)}
