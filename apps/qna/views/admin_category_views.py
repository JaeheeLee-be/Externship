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


class AdminCategoryCreateAPIView(APIView):
    permission_classes = [IsRoleAdminUser]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminCategoryCreateSerializer(data=request.data)

        if not serializer.is_valid():
            error_detail = serializer.get_error_detail()

            status_code: int

            if error_detail == "부모 카테고리를 찾을 수 없습니다.":
                status_code = status.HTTP_404_NOT_FOUND
            elif error_detail == "동일한 이름의 카테고리가 이미 존재합니다.":
                status_code = status.HTTP_409_CONFLICT
            else:
                status_code = status.HTTP_400_BAD_REQUEST

            return Response(
                {"error_detail": error_detail},
                status=status_code,
            )

        category = CategoryService.create_category(
            name=serializer.validated_data["name"],
            parent=serializer.validated_data.get("parent"),
        )

        response_serializer = AdminCategoryCreateResponseSerializer(category)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
