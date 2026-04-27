from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.exceptions import InvalidFileExtensionError
from apps.posts.serializers.post_crud_serializer import (
    ErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)
from apps.posts.serializers.presigned_url_serializer import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)
from apps.posts.services.presigned_url_service import generate_presigned_url


class PresignedUrlView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["posts"],
        summary="S3 게시글 이미지 업로드용 presigned URL 발급",
        request=PresignedUrlRequestSerializer,
        responses={
            200: PresignedUrlResponseSerializer,
            400: ValidationErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PresignedUrlRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = generate_presigned_url(file_name=serializer.validated_data["file_name"])
        except InvalidFileExtensionError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)
