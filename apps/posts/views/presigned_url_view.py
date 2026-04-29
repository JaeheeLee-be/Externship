from rest_framework.permissions import IsAuthenticated

from apps.core.utils.s3 import PresignedUrlView


class PostPresignedUrlView(PresignedUrlView):
    permission_classes = [IsAuthenticated]
    path = "uploads/images/posts/"
