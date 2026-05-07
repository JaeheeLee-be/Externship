from typing import Never, cast

from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.exceptions import (
    CommentNotFoundError,
    CommentPermissionDeniedError,
    PostNotFoundError,
)
from apps.posts.serializers.comment_serializer import (
    CommentCreateSerializer,
    CommentQuerySerializer,
    PostCommentSerializer,
)
from apps.posts.services import comment_service as comment_service
from apps.users.models import User


class CommentListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated(detail="자격 인증 데이터가 제공되지 않았습니다.", code=code)
        raise exceptions.PermissionDenied(detail="권한이 없습니다.", code=code)

    @extend_schema(
        tags=["comments"],
        summary="댓글 목록 조회",
        responses={200: PostCommentSerializer(many=True), 404: None},
    )
    def get(self, request: Request, post_id: int) -> Response:
        query_serializer = CommentQuerySerializer(data=request.query_params)
        query_serializer.is_valid()
        page = query_serializer.validated_data["page"]
        page_size = query_serializer.validated_data["page_size"]

        try:
            data = comment_service.get_comments(
                post_id=post_id,
                page=page,
                page_size=page_size,
                base_url=request.build_absolute_uri(request.path),
            )
        except PostNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "count": data["count"],
                "next": data["next"],
                "previous": data["previous"],
                "results": PostCommentSerializer(data["results"], many=True).data,
            }
        )

    @extend_schema(
        tags=["comments"],
        summary="댓글 작성",
        request=CommentCreateSerializer,
        responses={201: None, 400: None, 401: None, 404: None},
    )
    def post(self, request: Request, post_id: int) -> Response:
        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            comment_service.create_comment(
                user=cast(User, request.user),
                post_id=post_id,
                content=serializer.validated_data["content"],
                tagged_user_ids=serializer.validated_data.get("tagged_user_ids", []),
            )
        except PostNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "댓글이 등록되었습니다."}, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        if not request.successful_authenticator:
            raise exceptions.NotAuthenticated(detail="자격 인증 데이터가 제공되지 않았습니다.", code=code)
        raise exceptions.PermissionDenied(detail="권한이 없습니다.", code=code)

    @extend_schema(
        tags=["comments"],
        summary="댓글 삭제",
        responses={200: None, 401: None, 403: None, 404: None},
    )
    def delete(self, request: Request, post_id: int, comment_id: int) -> Response:
        try:
            comment_service.delete_comment(user=cast(User, request.user), comment_id=comment_id, post_id=post_id)
        except CommentNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except CommentPermissionDeniedError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response({"detail": "댓글이 삭제되었습니다."}, status=status.HTTP_200_OK)
