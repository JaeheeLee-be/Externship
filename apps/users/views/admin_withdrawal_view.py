from __future__ import annotations

from typing import NoReturn

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.users.serializers.admin_withdrawal_serializer import (
    WithdrawalListQuerySerializer,
    WithdrawalListResponseSerializer,
    WithdrawalListSerializer,
)
from apps.users.services.admin_withdrawal_service import get_withdrawal_list


class AdminWithdrawalPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminWithdrawalListView(APIView):
    permission_classes = [IsRoleAdminUser]
    serializer_class = WithdrawalListSerializer

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> NoReturn:
        if not request.user.is_authenticated:
            raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")
        raise PermissionDenied("권한이 없습니다.")

    @extend_schema(
        tags=["admin"],
        summary="어드민 회원 탈퇴 내역 목록 조회",
        description="어드민이 회원 탈퇴 내역을 페이지네이션, 검색, 역할, 정렬 조건으로 조회합니다.",
        parameters=[WithdrawalListQuerySerializer],
        responses={
            200: WithdrawalListResponseSerializer,
            401: OpenApiResponse(
                description="인증 실패",
                response=serializers.Serializer,
            ),
            403: OpenApiResponse(
                description="권한 없음",
                response=serializers.Serializer,
            ),
        },
    )
    def get(self, request: Request) -> Response:
        query_serializer = WithdrawalListQuerySerializer(data=request.query_params)
        query_serializer.is_valid()

        queryset = get_withdrawal_list(
            search=query_serializer.validated_data.get("search"),
            role=query_serializer.validated_data.get("role"),
            sort=query_serializer.validated_data.get("sort"),
        )
        paginator = AdminWithdrawalPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = WithdrawalListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
