from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.enrollment_serializer import EnrollmentSerializer
from apps.users.services.enrollment_service import create_enrollment


class EnrollmentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="수강생 등록 신청 API",
        description="로그인한 유저만 과정과 기수를 선택하여 수강생 등록 신청할 수 있습니다",
        request=EnrollmentSerializer,
        responses={
            201: OpenApiResponse(description="수강생 등록 신청완료."),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증 실패"),
        },
    )
    def post(self, request: Request) -> Response:
        user = request.user
        # mypy에서 IsAuthenticated 못 읽어서 추가함
        # user가 User 객체면 True, AnonymousUser면 False
        if not isinstance(user, User):
            return Response({"error_detail": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = EnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                create_enrollment(user=user, validated_data=serializer.validated_data)
                return Response({"detail": "수강생 등록 신청완료."}, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({"error_detail": str(e.detail)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
