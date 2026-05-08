from typing import NoReturn, cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.exceptions import PostNotFoundError, PostPermissionDeniedError
from apps.posts.serializers.post_crud_serializer import (
    ErrorResponseSerializer,
    PostCreateRequestSerializer,
    PostCreateResponseSerializer,
    PostDeleteResponseSerializer,
    PostDetailResponseSerializer,
    PostListResponseSerializer,
    PostUpdateRequestSerializer,
    PostUpdateResponseSerializer,
    ValidationErrorResponseSerializer,
)
from apps.posts.services import post_crud_service as postcrud_service
from apps.users.models import User


class PostPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


# 목록 응답용 시리얼라이저 추후에 추가해서 수정할 예정
class PostListCreateView(APIView):

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def permission_denied(
        self,
        request: Request,
        message: str | None = None,
        code: str | None = None,
    ) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["posts"],
        summary="글 목록 조회",
        responses={200: PostListResponseSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        category_id = request.query_params.get("category_id")

        posts = postcrud_service.list_posts(
            search=request.query_params.get("search"),
            search_filter=request.query_params.get("search_filter"),
            category_id=int(category_id) if category_id else None,
            sort=request.query_params.get("sort", "latest"),
        )

        paginator = PostPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = PostListResponseSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

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
        serializer = PostCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post = postcrud_service.create_post(author=cast(User, request.user), validated_data=serializer.validated_data)
        return Response(
            PostCreateResponseSerializer({"pk": post.id}).data,
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(APIView):

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def permission_denied(
        self,
        request: Request,
        message: str | None = None,
        code: str | None = None,
    ) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("권한이 없습니다.")

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
            post = postcrud_service.get_post(post_id)
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
        serializer = PostUpdateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            updated_post = postcrud_service.update_post(
                post_id=post_id,
                user=cast(User, request.user),
                validated_data=serializer.validated_data,
            )
        except PostNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PostPermissionDeniedError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
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
        try:
            postcrud_service.delete_post(
                post_id=post_id,
                user=cast(User, request.user),
            )
        except PostNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PostPermissionDeniedError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            PostDeleteResponseSerializer().data,
            status=status.HTTP_200_OK,
        )
