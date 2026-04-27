from django.urls import path

from apps.posts.views.presigned_url_view import PresignedUrlView

urlpatterns = [
    path("presigned-url/", PresignedUrlView.as_view(), name="presigned_url"),
]
