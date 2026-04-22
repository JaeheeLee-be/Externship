from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.exceptions import PostNotFoundError, PostPermissionDeniedError
from apps.posts.serializers.post_crud import (
    ErrorResponseSerializer,
    PostCreateRequestSerializer,
    PostCreateResponseSerializer,
    PostDeleteResponseSerializer,
    PostDetailResponseSerializer,
    PostUpdateRequestSerializer,
    PostUpdateResponseSerializer,
    ValidationErrorResponseSerializer,
)
from apps.posts.services import post_crud as post_service


class PostListCreateView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["posts"],
        summary="글 목록 조회",
        responses={200: PostDetailResponseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        posts = post_service.list_posts()
        return Response(
            PostDetailResponseSerializer(posts, many=True).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 작성",
        request=PostCreateRequestSerializer,
        responses={
            201: PostCreateResponseSerializer,
            400: ValidationErrorResponseSerializer,
            401: ErrorResponseSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = PostCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post = post_service.create_post(author=request.user, validated_data=serializer.validated_data)
        return Response(
            {"detail": "게시글이 성공적으로 등록되었습니다.", "pk": post.id},
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["posts"],
        summary="글 상세 조회",
        responses={
            200: PostDetailResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request, post_id: int) -> Response:
        try:
            post = post_service.get_post(post_id)
        except PostNotFoundError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            PostDetailResponseSerializer(post).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 수정",
        request=PostUpdateRequestSerializer,
        responses={
            200: PostUpdateResponseSerializer,
            400: ValidationErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def put(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = PostUpdateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            updated_post = post_service.update_post(
                post_id=post_id,
                user=request.user,
                validated_data=serializer.validated_data,
            )
        except PostNotFoundError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PostPermissionDeniedError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            PostUpdateResponseSerializer(updated_post).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["posts"],
        summary="글 삭제",
        responses={
            200: PostDeleteResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def delete(self, request: Request, post_id: int) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            post_service.delete_post(post_id=post_id, user=request.user)
        except PostNotFoundError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PostPermissionDeniedError as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {"detail": "게시글이 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )
