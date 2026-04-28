from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request

from apps.core.presigned_url.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)
from apps.core.presigned_url.views import PresignedUrlView
from apps.core.utils.permissions import IsRoleAdminUser
from apps.exams.serializers.exam_presigned_url_serializer import (
    ExamErrorResponseSerializer,
)


class ExamPresignedUrlView(PresignedUrlView):
    permission_classes = [IsRoleAdminUser]
    path = "uploads/exams/thumbnails"

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("로그인이 필요합니다.")
        raise PermissionDenied("관리자 권한이 필요합니다.")

    @extend_schema(
        tags=["exams"],
        summary="exams presigned_url",
        request=PresignedUrlRequestSerializer,
        responses={
            200: PresignedUrlResponseSerializer,
            400: OpenApiResponse(
                description="error_detail: 파일을 첨부해주세요, 지원하지 않는 파일 형식입니다.",
                response=ExamErrorResponseSerializer,
            ),
            401: ExamErrorResponseSerializer,
            403: ExamErrorResponseSerializer,
        },
    )
    def put(self, request: Request):
        return self.handle_request(request)
