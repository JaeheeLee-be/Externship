from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Post
from apps.posts.serializers.post_crud import (
    PostCreateRequestSerializer,
    PostCUDResponseSerializer,
    PostUpdateRequestSerializer,
)


class PostCreateView(APIView):
    @extend_schema(
        tags=["posts"],
        summary="글 작성",
        request=PostCreateRequestSerializer,
        responses={201: PostCUDResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = PostCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        return Response(
            PostCUDResponseSerializer(post).data,
            status=status.HTTP_201_CREATED,
        )


class PostUpdateView(APIView):
    @extend_schema(
        tags=["posts"],
        summary="글 수정",
        request=PostUpdateRequestSerializer,
        responses={200: PostCUDResponseSerializer},
    )
    def patch(self, request: Request, post_id: int) -> Response:
        post = Post.objects.get(id=post_id)

        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = PostUpdateRequestSerializer(
            instance=post,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        updated_post = serializer.save()

        return Response(
            PostCUDResponseSerializer(updated_post).data,
            status=status.HTTP_200_OK,
        )


class PostDeleteView(APIView):
    @extend_schema(
        tags=["posts"],
        summary="글 삭제",
        responses={204: None},
    )
    def delete(self, request: Request, post_id: int) -> Response:
        post = Post.objects.get(id=post_id)

        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        post.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
