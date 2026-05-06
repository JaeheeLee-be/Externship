from typing import Any, NoReturn

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsStudentUser
from apps.qna.serializers.category_serializers import CategoryTreeSerializer
from apps.qna.services.category_services import CategoryService


class CategoryListAPIView(APIView):
    permission_classes = [IsStudentUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="로그인이 필요합니다.")
        raise PermissionDenied(detail="카테고리 조회 권한이 없습니다.")

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        categories = CategoryService.get_category_tree()

        return Response(
            {"categories": CategoryTreeSerializer(categories, many=True).data},
            status=status.HTTP_200_OK,
        )
