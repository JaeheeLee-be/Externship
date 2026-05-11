from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from apps.core.presigned_url.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)
from apps.core.utils.s3 import PresignedUrlView


@extend_schema(
    request=PresignedUrlRequestSerializer,
    responses={200: PresignedUrlResponseSerializer},
    summary="게시글 이미지 presigned URL 발급",
    tags=["posts"],
)
class PostPresignedUrlView(PresignedUrlView):
    permission_classes = [IsAuthenticated]
    path = "uploads/images/posts/"

    # def post(self, request, *args, **kwargs):
    #     return super().post(request, *args, **kwargs)
