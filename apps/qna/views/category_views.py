from typing import Any

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qna.serializers.category_serializers import (
    AdminCategoryCreateSerializer,
    AdminCategoryCreateResponseSerializer,
)
from apps.qna.services.category_services import CategoryService


class AdminCategoryCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminCategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = CategoryService.create_category(
            name=serializer.validated_data["name"],
            parent=serializer.validated_data.get("parent"),
        )

        response_serializer = AdminCategoryCreateResponseSerializer(category)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)