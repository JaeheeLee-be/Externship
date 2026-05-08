from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.check_nickname_serializer import CheckNicknameSerializer
from apps.users.utils.user_exceptions import DuplicateNicknameError


class CheckNicknameView(APIView):
    permission_classes = [AllowAny]  # 회원가입(로그인전), 내 정보수정(로그인후) 두 가지 경우라서

    @extend_schema(
        tags=["accounts"],
        summary="닉네임 중복 확인 API",
        description="로그인 유저는 닉네임 중복 확인 검사 가능",
        request=CheckNicknameSerializer,
        responses={
            200: CheckNicknameSerializer,
            400: OpenApiResponse(description="이 필드는 필수 항목입니다."),
            409: OpenApiResponse(description="중복된 닉네임이 존재합니다."),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = CheckNicknameSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response({"detail": "사용 가능한 닉네임입니다."}, status=status.HTTP_200_OK)
        except DuplicateNicknameError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_409_CONFLICT)
        except ValidationError:
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
