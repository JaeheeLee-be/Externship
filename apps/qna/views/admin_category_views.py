from typing import Any, NoReturn

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.qna.exceptions import BaseCustomException
from apps.qna.serializers.category_serializers import (
    AdminCategoryCreateResponseSerializer,
    AdminCategoryCreateSerializer,
    AdminCategoryListQuerySerializer,
    AdminCategoryListSerializer,
)
from apps.qna.services.admin_category_services import CategoryService


class AdminCategoryListCreateAPIView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="로그인이 필요합니다.")
        raise PermissionDenied(
            detail=(
                "카테고리 목록 조회 권한이 없습니다." if request.method == "GET" else "카테고리 등록 권한이 없습니다."
            )
        )

    # 생성
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            serializer = AdminCategoryCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error_detail": serializer.get_error_detail()},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            category = CategoryService.create_category(
                name=serializer.validated_data["name"],
                parent=serializer.validated_data.get("parent"),
            )
            return Response(
                AdminCategoryCreateResponseSerializer(category).data,
                status=status.HTTP_201_CREATED,
            )
        except BaseCustomException as e:
            return Response(
                {"error_detail": e.message},
                status=e.status_code,
            )

    # 조회
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AdminCategoryListQuerySerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                {"error_detail": "유효하지 않은 목록 조회 요청입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        categories, total_count = CategoryService.get_category_list(
            page=data["page"],
            page_size=data["page_size"],
            search_keyword=data.get("search_keyword"),
            category_type=data.get("category_type"),
        )

        return Response(
            {
                "page": data["page"],
                "page_size": data["page_size"],
                "total_count": total_count,
                "categories": AdminCategoryListSerializer(categories, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminCategoryDestroyAPIView(APIView):
    permission_classes = [IsRoleAdminUser]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated(detail="로그인이 필요합니다.")
        raise PermissionDenied(detail="카테고리 삭제 권한이 없습니다.")

    # 삭제
    def delete(self, request: Request, category_id: int, *args: Any, **kwargs: Any) -> Response:
        try:
            result = CategoryService.delete_category(category_id=category_id)
            return Response(result, status=status.HTTP_200_OK)
        except BaseCustomException as e:
            return Response({"error_detail": e.message}, status=e.status_code)
