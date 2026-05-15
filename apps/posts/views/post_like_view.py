from typing import NoReturn, cast

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.exceptions import (
    PostAlreadyLikedError,
    PostLikeNotRegisteredError,
    PostLikePostNotFoundError,
)
from apps.posts.serializers.post_like_serializer import PostLikeResponseSerializer
from apps.posts.services.post_like_service import cancel_post_like, create_post_like
from apps.users.models import User


class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(
        self,
        request: Request,
        message: str | None = None,
        code: str | None = None,
    ) -> NoReturn:
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["posts"],
        summary="게시글 좋아요 생성",
        description="게시글 좋아요를 생성하거나 취소된 좋아요를 다시 활성화",
        responses={
            201: OpenApiResponse(
                description="좋아요 등록 성공",
                examples=[OpenApiExample(name="성공 응답", value={"detail": "좋아요가 등록되었습니다."})],
            ),
            401: OpenApiResponse(
                description="인증되지 않은 요청",
                examples=[
                    OpenApiExample(name="인증 실패", value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})
                ],
            ),
            404: OpenApiResponse(
                description="게시글 없음 또는 숨김 처리된 게시글",
                examples=[
                    OpenApiExample(name="게시글 없음", value={"error_detail": "해당 게시글을 찾을 수 없습니다."})
                ],
            ),
            409: OpenApiResponse(
                description="이미 좋아요한 게시글",
                examples=[
                    OpenApiExample(name="중복 좋아요", value={"error_detail": "이미 좋아요를 누른 게시글입니다."})
                ],
            ),
        },
    )
    def post(self, request: Request, post_id: int) -> Response:
        try:
            result = create_post_like(user=cast(User, request.user), post_id=post_id)
        except PostLikePostNotFoundError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PostAlreadyLikedError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(PostLikeResponseSerializer(result).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["posts"],
        summary="게시글 좋아요 취소",
        description="게시글 좋아요를 취소합니다. 단, row를 삭제하지 않고 is_liked 필드를 False로 변경합니다.",
        responses={
            200: OpenApiResponse(
                description="좋아요 취소 성공",
                examples=[OpenApiExample(name="성공 응답", value={"detail": "좋아요가 취소되었습니다."})],
            ),
            401: OpenApiResponse(
                description="인증되지 않은 요청",
                examples=[
                    OpenApiExample(name="인증 실패", value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})
                ],
            ),
            404: OpenApiResponse(
                description="게시글 없음, 숨김 게시글, 또는 좋아요 기록 없음",
                examples=[
                    OpenApiExample(name="게시글 없음", value={"error_detail": "해당 게시글을 찾을 수 없습니다."}),
                    OpenApiExample(name="좋아요 기록 없음", value={"error_detail": "좋아요 기록을 찾을 수 없습니다."}),
                ],
            ),
        },
    )
    def delete(self, request: Request, post_id: int) -> Response:
        try:
            result = cancel_post_like(user=cast(User, request.user), post_id=post_id)
        except (PostLikePostNotFoundError, PostLikeNotRegisteredError) as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(PostLikeResponseSerializer(result).data, status=status.HTTP_200_OK)
