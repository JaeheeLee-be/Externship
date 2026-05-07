from django.http import HttpRequest, HttpResponseBase
from django.urls import path

from apps.posts.views.post_crud import (
    PostDetailView,
    PostListCreateView,
)

# def post_list_or_create(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponseBase:
#     if request.method == "POST":
#         return PostCreateView.as_view()(request, *args, **kwargs)
#     return PostListView.as_view()(request, *args, **kwargs)
#
#
# def post_detail_update_delete(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponseBase:
#     if request.method == "PUT":
#         return PostUpdateView.as_view()(request, *args, **kwargs)
#     if request.method == "DELETE":
#         return PostDeleteView.as_view()(request, *args, **kwargs)
#     return PostDetailView.as_view()(request, *args, **kwargs)


urlpatterns = [
    path("", PostListCreateView.as_view(), name="post_list_create"),
    path("<int:post_id>", PostDetailView.as_view(), name="post_detail"),
]
