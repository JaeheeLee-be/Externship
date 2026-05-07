from typing import Never

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.check_nickname_serializer import CheckNicknameSerializer
from apps.users.utils.user_exceptions import DuplicateNicknameError


class CheckNicknameView(APIView):
    permission_classes = [IsAuthenticated]

    def permission_denied(self, request: Request, message: str | None = None, code: str | None = None) -> Never:
        raise NotAuthenticated("자격 인증 데이터가 제공되지 않았습니다.")

    @extend_schema(
        tags=["accounts"],
        summary="닉네임 중복 확인 API",
        description="로그인한 유저는 회원정보 조회가능, 수강생 등록이 되어있을 경우 수강중 과정, 기수도 조회가능",
        responses={
            200: CheckNicknameSerializer,
            400: OpenApiResponse(description="이 필드는 필수 항목입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
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
