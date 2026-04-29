from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.qna.serializers.category_serializers import (
    AdminCategoryCreateResponseSerializer,
    AdminCategoryCreateSerializer,
    AdminCategoryListQuerySerializer,
    AdminCategoryListSerializer,
)
from apps.qna.services.admin_category_services import CategoryService

ERROR_STATUS_MAP = {
    "parent_not_found": status.HTTP_404_NOT_FOUND,
    "duplicate_category": status.HTTP_409_CONFLICT,
    "large_has_parent": status.HTTP_400_BAD_REQUEST,
    "invalid_middle_parent": status.HTTP_400_BAD_REQUEST,
    "invalid_small_parent": status.HTTP_400_BAD_REQUEST,
}


class AdminCategoryListCreateAPIView(APIView):
    permission_classes = [IsRoleAdminUser]

    # 생성
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

    # 조회
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminCategoryListQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        categories, total_count = CategoryService.get_category_list(
            page=data["page"],
            page_size=data["page_size"],
            search_keyword=data.get("search_keyword"),
            category_type=data.get("category_type"),
        )

        return Response(
            {
                "page": data["page"],
                "page_size": data["page_size"],
                "total_count": total_count,
                "categories": AdminCategoryListSerializer(categories, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
