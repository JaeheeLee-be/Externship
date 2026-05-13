from django.urls import path

from apps.posts.views.post_comment_view import CommentDetailView, CommentListCreateView

urlpatterns = [
    path("<int:post_id>/comments", CommentListCreateView.as_view(), name="comment_list_create"),
    path("<int:post_id>/comments/<int:comment_id>", CommentDetailView.as_view(), name="comment_detail"),
]
