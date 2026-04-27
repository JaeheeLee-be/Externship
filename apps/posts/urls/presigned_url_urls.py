from apps.posts.views.presigned_url_view import PresignedUrlView
from django.urls import path

urlpatterns = [
    path("presigned-url/", PresignedUrlView.as_view(), name="presigned_url"),
]