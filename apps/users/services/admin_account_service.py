from typing import Any

from django.db.models import Q, QuerySet

from apps.users.models import User


class AdminAccountService:

    @staticmethod
    def get_account_list(validated_params: dict[str, Any]) -> dict[str, Any]:
        queryset: QuerySet[User] = User.objects.all().order_by("-created_at")

        # 이메일 또는 닉네임 검색
        if search := validated_params.get("search"):
            queryset = queryset.filter(Q(email__icontains=search) | Q(nickname__icontains=search))

        if status := validated_params.get("status"):
            if status == "active":
                queryset = queryset.filter(is_active=True)
            elif status == "inactive":
                queryset = queryset.filter(is_active=False)
            elif status == "withdrew":
                queryset = queryset.filter(withdrawal__isnull=False)

        if role := validated_params.get("role"):
            queryset = queryset.filter(role=role.upper())

        page: int = validated_params.get("page", 1)
        page_size: int = validated_params.get("page_size", 10)
        offset: int = (page - 1) * page_size

        total_count: int = queryset.count()
        results = queryset[offset : offset + page_size]

        return {
            "count": total_count,
            "results": results,
            "page": page,
            "page_size": page_size,
        }
