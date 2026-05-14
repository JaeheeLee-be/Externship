from typing import Any

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.schemas.category_schemas import category_list_schema
from apps.qna.serializers.category_serializers import CategoryTreeSerializer
from apps.qna.services.category_services import CategoryService


class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    @category_list_schema
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        categories = CategoryService.get_category_tree()

        return Response(
            {"categories": CategoryTreeSerializer(categories, many=True).data},
            status=status.HTTP_200_OK,
        )
