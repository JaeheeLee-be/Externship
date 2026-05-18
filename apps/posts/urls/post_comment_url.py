from django.urls import path

from apps.posts.views.post_comment_view import (
    CommentDetailView,
    CommentListCreateView,
    ReplyCreateView,
)

urlpatterns = [
    path("<int:post_id>/comments", CommentListCreateView.as_view(), name="comment_list_create"),
    path("<int:post_id>/comments/<int:comment_id>", CommentDetailView.as_view(), name="comment_detail"),
    path("<int:post_id>/comments/<int:comment_id>/replies", ReplyCreateView.as_view(), name="reply_create"),
]
