from typing import Any

from django.db.models import Q, QuerySet
from django.http import QueryDict

from apps.users.models import User


class AdminAccountService:

    @staticmethod
    def get_account_list(
        validated_params: dict[str, Any],
        base_url: str,
        query_params: QueryDict,
    ) -> dict[str, Any]:
        queryset: QuerySet[User] = User.objects.all().order_by("-created_at")

        # 이메일 또는 닉네임 검색
        if search := validated_params.get("search"):
            queryset = queryset.filter(Q(email__icontains=search) | Q(nickname__icontains=search))

        if "is_active" in validated_params:
            queryset = queryset.filter(is_active=validated_params["is_active"])

        if role := validated_params.get("role"):
            queryset = queryset.filter(role=role)

        page: int = validated_params.get("page", 1)
        page_size: int = validated_params.get("page_size", 10)
        offset: int = (page - 1) * page_size

        total_count: int = queryset.count()
        results = queryset[offset : offset + page_size]

        # next / previous URL 구성 (기존 쿼리파라미터 유지)
        params = query_params.copy()
        params["page_size"] = str(page_size)

        params["page"] = str(page + 1)
        next_url = f"{base_url}?{params.urlencode()}" if (page * page_size) < total_count else None

        params["page"] = str(page - 1)
        previous_url = f"{base_url}?{params.urlencode()}" if page > 1 else None

        return {
            "count": total_count,
            "next": next_url,
            "previous": previous_url,
            "results": results,
        }
