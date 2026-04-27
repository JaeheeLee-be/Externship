from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.services.presigned_url_service import generate_presigned_url


class PresignedUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_name = request.data.get("file_name")
        if not file_name:
            raise ValidationError("file_name은 필수입니다.")

        try:
            result = generate_presigned_url(file_name=file_name)
        except ValueError as e:
            raise ValidationError(str(e))

        return Response(result, status=status.HTTP_200_OK)
