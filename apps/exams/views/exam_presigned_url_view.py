from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.presigned_url.serializers import PresignedUrlResponseSerializer
from apps.core.presigned_url.views import PresignedUrlView
from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.serializers.exam_presigned_url_serializer import (
    ExamErrorResponseSerializer,
    ExamPresignedUrlRequestSerializer,
)


class ExamPresignedUrlView(PresignedUrlView):
    permission_classes = [IsRoleAdminUser]
    path = "uploads/exams/thumbnails"
    request_serializer_class = ExamPresignedUrlRequestSerializer

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("로그인이 필요합니다.")
        raise PermissionDenied("관리자 권한이 필요합니다.")

    @extend_schema(
        tags=["exams"],
        summary="exams presigned_url",
        request=ExamPresignedUrlRequestSerializer,
        responses={
            200: PresignedUrlResponseSerializer,
            400: OpenApiResponse(
                description="error_detail: 지원하지 않는 파일 형식입니다.",
                response=ExamErrorResponseSerializer,
            ),
            401: ExamErrorResponseSerializer,
            403: ExamErrorResponseSerializer,
        },
    )
    # 에러메시지 error_detail로 출력하기 위해 추가
    def handle_request(self, request: Request) -> Response:
        ExamPresignedUrlRequestSerializer(data=request.data).is_valid(raise_exception=True)
        return super().handle_request(request)

    def put(self, request: Request) -> Response:
        return self.handle_request(request)
