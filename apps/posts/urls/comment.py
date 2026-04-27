from django.urls import path

from apps.posts.views.comment import CommentDetailView, CommentListCreateView

urlpatterns = [
    path("<int:post_id>/comments/", CommentListCreateView.as_view()),
    path("<int:post_id>/comments/<int:comment_id>/", CommentDetailView.as_view()),
]
