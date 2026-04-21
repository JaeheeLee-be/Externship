from django.urls import path

from apps.posts.views.post_crud import (
    PostCreateView,
    PostDeleteView,
    PostUpdateView,
)

urlpatterns = [
    path("", PostCreateView.as_view(), name="create_post"),
    path("update/<int:post_id>", PostUpdateView.as_view(), name="update_post"),
    path("delete/<int:post_id>", PostDeleteView.as_view(), name="delete_post"),
]
