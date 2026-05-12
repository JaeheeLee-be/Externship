from django.urls import path

from apps.posts.views.post_like_view import PostLikeCancelView, PostLikeCreateView

urlpatterns = [
    path(
        "<int:post_id>/like/cancel",
        PostLikeCancelView.as_view(),
        name="post-like-cancel",
    ),
    path(
        "<int:post_id>/like",
        PostLikeCreateView.as_view(),
        name="post-like-create",
    ),
]
