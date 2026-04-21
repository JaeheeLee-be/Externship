from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Post
from apps.posts.serializers.post_crud import (
    PostCreateRequestSerializer,
    PostCreateResponseSerializer,
    PostDeleteResponseSerializer,
    PostDetailResponseSerializer,
    PostUpdateRequestSerializer,
    PostUpdateResponseSerializer,
)


def _get_post_or_404(post_id: int) -> Post:
    try:
        return Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        raise NotFound("해당 게시글을 찾을 수 없습니다.")


class PostListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["posts"],
        summary="글 목록 조회",
        responses={200: PostDetailResponseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        posts = Post.objects.all()
        return Response(
            PostDetailResponseSerializer(posts, many=True).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 작성",
        request=PostCreateRequestSerializer,
        responses={201: PostCreateResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = PostCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        return Response(
            {"detail": "게시글이 성공적으로 등록되었습니다.", "pk": post.id},
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["posts"],
        summary="글 상세 조회",
        responses={200: PostDetailResponseSerializer},
    )
    def get(self, request: Request, post_id: int) -> Response:
        post = _get_post_or_404(post_id)
        return Response(
            PostDetailResponseSerializer(post).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 수정",
        request=PostUpdateRequestSerializer,
        responses={200: PostUpdateResponseSerializer},
    )
    def put(self, request: Request, post_id: int) -> Response:
        post = _get_post_or_404(post_id)

        if post.author != request.user:
            raise PermissionDenied("권한이 없습니다.")

        serializer = PostUpdateRequestSerializer(instance=post, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_post = serializer.save()

        return Response(
            PostUpdateResponseSerializer(updated_post).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 삭제",
        responses={200: PostDeleteResponseSerializer},
    )
    def delete(self, request: Request, post_id: int) -> Response:
        post = _get_post_or_404(post_id)

        if post.author != request.user:
            raise PermissionDenied("권한이 없습니다.")

        post.delete()
        return Response(
            {"detail": "게시글이 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )
