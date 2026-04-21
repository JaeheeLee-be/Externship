from django.urls import path

from apps.posts.views.post_crud import PostDetailView, PostListCreateView

urlpatterns = [
    path("", PostListCreateView.as_view(), name="post_list_create"),
    path("<int:post_id>", PostDetailView.as_view(), name="post_detail"),
]
