from django.db.models import Q, QuerySet

from apps.users.models import User


class AdminAccountService:

    @staticmethod
    def get_account_list(validated_params: dict) -> dict:
        queryset: QuerySet = User.objects.all().order_by("-created_at")

        # 이메일 또는 닉네임 검색
        if search := validated_params.get("search"):
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(nickname__icontains=search)
            )

        if status := validated_params.get("status"):
            queryset = queryset.filter(status=status)

        if role := validated_params.get("role"):
            queryset = queryset.filter(role=role)

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
