from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.exceptions import CommentNotFoundError, CommentPermissionDeniedError
from apps.posts.models.post import Post
from apps.posts.serializers.comment import (
    CommentCreateSerializer,
    PostCommentSerializer,
)
from apps.posts.services import comment as comment_service
from apps.users.models import User


class CommentListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["comments"],
        summary="댓글 목록 조회",
        responses={200: PostCommentSerializer(many=True), 404: None},
    )
    def get(self, request: Request, post_id: int) -> Response:
        if not Post.objects.filter(id=post_id).exists():
            return Response({"error_detail": "해당 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        total_count, comments = comment_service.get_comments(post_id, page, page_size)

        base_url = request.build_absolute_uri(request.path)
        next_page = f"{base_url}?page={page + 1}&page_size={page_size}" if (page * page_size) < total_count else None
        previous_page = f"{base_url}?page={page - 1}&page_size={page_size}" if page > 1 else None

        return Response(
            {
                "count": total_count,
                "next": next_page,
                "previous": previous_page,
                "results": PostCommentSerializer(comments, many=True).data,
            }
        )

    @extend_schema(
        tags=["comments"],
        summary="댓글 작성",
        request=CommentCreateSerializer,
        responses={201: None, 400: None, 401: None, 404: None},
    )
    def post(self, request: Request, post_id: int) -> Response:
        if not Post.objects.filter(id=post_id).exists():
            return Response({"error_detail": "해당 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        comment_service.create_comment(
            user=cast(User, request.user),
            post_id=post_id,
            content=serializer.validated_data["content"],
            tagged_user_ids=serializer.validated_data.get("tagged_user_ids", []),
        )

        return Response({"detail": "댓글이 등록되었습니다."}, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

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
