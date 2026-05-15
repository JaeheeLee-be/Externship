from django.urls import path

from apps.posts.views.post_like_view import PostLikeView

urlpatterns = [
    path("<int:post_id>/like", PostLikeView.as_view(), name="post-like"),
]
