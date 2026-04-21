from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Post
from apps.posts.serializers.post_crud import (
    PostCreateRequestSerializer,
    PostCUDResponseSerializer,
    PostUpdateRequestSerializer,
)


class PostListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["posts"],
        summary="글 목록 조회",
        responses={200: PostCUDResponseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        posts = Post.objects.all()
        return Response(
            PostCUDResponseSerializer(posts, many=True).data,
            status=status.HTTP_200_OK,
        )

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


class PostDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["posts"],
        summary="글 상세 조회",
        responses={200: PostCUDResponseSerializer},
    )
    def get(self, request: Request, post_id: int) -> Response:
        post = get_object_or_404(Post, id=post_id)
        return Response(
            PostCUDResponseSerializer(post).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 수정",
        request=PostUpdateRequestSerializer,
        responses={200: PostCUDResponseSerializer},
    )
    def patch(self, request: Request, post_id: int) -> Response:
        post = get_object_or_404(Post, id=post_id)

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

    @extend_schema(
        tags=["posts"],
        summary="글 삭제",
        responses={204: None},
    )
    def delete(self, request: Request, post_id: int) -> Response:
        post = get_object_or_404(Post, id=post_id)

        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
