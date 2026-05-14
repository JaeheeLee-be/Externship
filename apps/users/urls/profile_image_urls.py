from django.urls import path
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from apps.core.presigned_url.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)
from apps.core.presigned_url.views import PresignedUrlView
from apps.users.views.profile_image_views import ProfileImageView


@extend_schema(
    tags=["accounts"],
    summary="프로필 이미지 presigned URL 발급",
    request=PresignedUrlRequestSerializer,
    responses={200: PresignedUrlResponseSerializer},
)
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
