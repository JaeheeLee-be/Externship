from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.serializers.notification_serializer import NotificationSerializer
from apps.posts.services import notification_service
from apps.users.models import User


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["notifications"],
        summary="알림 목록 조회",
        responses={200: NotificationSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        data = notification_service.get_notifications(user)
        return Response(
            {
                "unread_count": data["unread_count"],
                "results": NotificationSerializer(data["notifications"], many=True).data,
            }
        )

    @extend_schema(
        tags=["notifications"],
        summary="알림 전체 읽음 처리",
        responses={200: None},
    )
    def patch(self, request: Request) -> Response:
        notification_service.mark_notifications_read(cast(User, request.user))
        return Response({"detail": "모든 알림을 읽음 처리했습니다."}, status=status.HTTP_200_OK)
