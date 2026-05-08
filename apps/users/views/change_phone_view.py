from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.change_phone_serializer import ChangePhoneSerializer
from apps.users.services.change_phone_service import change_phone_service
from apps.users.utils.user_exceptions import ConflictError


class ChangePhoneView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["accounts"],
        summary="휴대폰 번호 변경 api",
        description="sms 인증 후 발급받은 토큰을 활용하여 휴대폰 번호 변경",
        request=ChangePhoneSerializer,
        responses={
            200: OpenApiResponse(description="휴대폰 번호 변경 성공"),
            400: OpenApiResponse(description="유효성 검사 실패"),
            401: OpenApiResponse(description="자격 인증 실패"),
            409: OpenApiResponse(description="이미 등록된 휴대폰 번호"),
        },
    )
    def patch(self, request: Request) -> Response:
        serializer = ChangePhoneSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = request.user
            assert isinstance(user, User)
            new_phone_number = change_phone_service(serializer.validated_data, user)
            return Response(
                {
                    "detail": "휴대폰 번호 변경에 성공하였습니다.",
                    "phone_number": new_phone_number,
                },
                status=status.HTTP_200_OK,
            )
        except ConflictError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError as e:
            return Response({"error_detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
