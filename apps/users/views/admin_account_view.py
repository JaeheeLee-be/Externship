from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.permissions import IsRoleAdminUser
from apps.users.serializers.admin_account_serializer import (
    AdminAccountQuerySerializer,
    AdminAccountSerializer,
)
from apps.users.services.admin_account_service import AdminAccountService


class AdminAccountListView(APIView):
    permission_classes = [IsRoleAdminUser]

    def get(self, request: Request) -> Response:
        # 쿼리 파라미터 검증
        query_serializer = AdminAccountQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        # 서비스 호출
        data = AdminAccountService.get_account_list(query_serializer.validated_data)

        # 응답 직렬화
        result_serializer = AdminAccountSerializer(data["results"], many=True)

        # next / previous URL 구성
        base_url = request.build_absolute_uri(request.path)
        page = data["page"]
        page_size = data["page_size"]
        count = data["count"]

        return Response(
            {
                "count": count,
                "next": f"{base_url}?page={page + 1}&page_size={page_size}" if (page * page_size) < count else None,
                "previous": f"{base_url}?page={page - 1}&page_size={page_size}" if page > 1 else None,
                "results": result_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
