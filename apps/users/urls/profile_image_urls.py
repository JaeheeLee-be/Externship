from django.urls import path

from apps.users.views.profile_image_views import (
    ProfileImagePresignedUrlView,
    ProfileImageView,
)

urlpatterns = [
    path("me/profile-image/presigned-url", ProfileImagePresignedUrlView.as_view(), name="profile-image-presigned-url"),
    path("me/profile-image", ProfileImageView.as_view(), name="profile-image"),
]
