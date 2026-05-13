from django.urls import path

from apps.posts.views.post_presigned_url_view import PostPresignedUrlView

urlpatterns = [
    path("presigned-url", PostPresignedUrlView.as_view(), name="presigned_url"),
]
