from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from apps.core.presigned_url.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)
from apps.core.utils.s3 import PresignedUrlView


@extend_schema(
    tags=["admin-courses"],
    summary="과정 이미지 presigned URL 발급",
    request=PresignedUrlRequestSerializer,
    responses={200: PresignedUrlResponseSerializer},
)
class CoursePresignedUrlView(PresignedUrlView):
    permission_classes = [IsAuthenticated]
    path = "uploads/images/courses/"
