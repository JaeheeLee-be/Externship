from django.urls import path
from rest_framework.permissions import IsAuthenticated

from apps.core.presigned_url.views import PresignedUrlView
from apps.users.views.profile_image_views import ProfileImageView


class ProfileImageUploadView(PresignedUrlView):
    path = "uploads/images/profiles"
    permission_classes = [IsAuthenticated]


urlpatterns = [
    path(
        "me/profile-image/presigned-url",
        ProfileImageUploadView.as_view(),
        name="profile-image-presigned-url",
    ),
    path(
        "me/profile-image",
        ProfileImageView.as_view(),
        name="profile-image",
    ),
]
