from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import PostCategory
from apps.posts.serializers.post_categories_serializer import (
    PostCategoryListResponseSerializer,
)


class PostCategoryListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["posts"],
        summary="커뮤니티 게시글 카테고리 목록 조회",
        responses={
            200: PostCategoryListResponseSerializer(many=True),
        },
    )
    def get(self, request: Request) -> Response:
        categories = PostCategory.objects.all().order_by("id")

        return Response(
            PostCategoryListResponseSerializer(categories, many=True).data,
            status=status.HTTP_200_OK,
        )
