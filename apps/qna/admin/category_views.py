from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.admin.category_services import AdminCategoryService
from apps.qna.serializers.category_serializers import AdminCategoryListSerializer


class AdminCategoryListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        category_type = request.query_params.get("category_type")
        keyword = request.query_params.get("keyword")

        categories = AdminCategoryService.get_category_list(
            category_type=category_type,
            keyword=keyword,
        )

        serializer = AdminCategoryListSerializer(categories, many=True)
        return Response(serializer.data)