from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.qna.serializers.category_serializers import (
    AdminCategoryCreateResponseSerializer,
    AdminCategoryCreateSerializer,
)
from apps.qna.services.admin_category_services import CategoryService

ERROR_STATUS_MAP = {
    "parent_not_found": status.HTTP_404_NOT_FOUND,
    "duplicate_category": status.HTTP_409_CONFLICT,
    "large_has_parent": status.HTTP_400_BAD_REQUEST,
    "invalid_middle_parent": status.HTTP_400_BAD_REQUEST,
    "invalid_small_parent": status.HTTP_400_BAD_REQUEST,
}


class AdminCategoryCreateAPIView(APIView):
    permission_classes = [IsRoleAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminCategoryCreateSerializer(data=request.data)

        if not serializer.is_valid():
            error_detail = serializer.get_error_detail()
            error_code = serializer.get_error_code()

            return Response(
                {"error_detail": error_detail},
                status=ERROR_STATUS_MAP.get(
                    error_code,
                    status.HTTP_400_BAD_REQUEST,
                ),
            )

        category = CategoryService.create_category(
            name=serializer.validated_data["name"],
            parent=serializer.validated_data.get("parent"),
        )

        response_serializer = AdminCategoryCreateResponseSerializer(category)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
