from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.profile_image_serializer import ProfileImageUpdateSerializer
from apps.users.services.profile_image_service import update_profile_image


class ProfileImageView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["accounts"], summary="프로필 이미지 URL 저장")
    def patch(self, request: Request) -> Response:
        serializer = ProfileImageUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user: User = request.user  # type: ignore[assignment]
        update_profile_image(user, serializer.validated_data["profile_img_url"])
        return Response({"detail": "프로필 사진이 등록되었습니다."}, status=status.HTTP_200_OK)
