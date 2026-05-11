from datetime import timedelta
from typing import Any, cast

from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers.user_login_serializer import (
    LoginSerializer,
    TokenRefreshSerializer,
)
from apps.users.services.user_login_service import UserLoginService
from apps.users.utils.user_exceptions import (
    InactiveError,
    InvalidLoginError,
    WithdrawnError,
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Account(로그인)"],
        summary="이메일 로그인 API",
        description="이메일과 비밀번호로 로그인합니다. Access 토큰은 바디로, Refresh 토큰은 쿠키로 반환됩니다.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="로그인 성공"),
            400: OpenApiResponse(description="유효성 검사 실패"),
            403: OpenApiResponse(description="비활성화 계정,탈퇴 계정,로그인 정보 불일치"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 데이터 검증 요청
        email = serializer.validated_data.get("email")
        password = serializer.validated_data.get("password")

        try:
            user = UserLoginService.verify_user(email, password)

        except WithdrawnError as e:
            return Response(
                {"error_detail": {"detail": str(e), "expire_at": e.expire_at}},  # 에러 객체에 담긴 날짜 활용
                status=status.HTTP_403_FORBIDDEN,
            )

        except (InvalidLoginError, InactiveError) as e:
            return Response(
                {"error_detail": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 토큰 생성 요청
        access_token, refresh_token = UserLoginService.generate_token_pair(user)

        # HTTP 응답 및 쿠키 설정
        response = Response({"access_token": access_token}, status=status.HTTP_200_OK)

        response.set_cookie(
            key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="None", path="/"
        )
        return response


class LogoutView(APIView):
    permission_classes: list[Any] = []

    @extend_schema(
        tags=["Account(로그인)"],
        summary="로그아웃 API",
        request=None,
        responses={200: OpenApiResponse(description="로그아웃 성공")},
    )
    def post(self, request: Request) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            # 블랙리스트 등록
            UserLoginService.add_to_blacklist(refresh_token)

        response = Response({"detail": "성공적으로 로그아웃 되었습니다."}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Account(로그인)"],
        summary="JWT 토큰 재발급 API",
        description="HttpOnly 쿠키의 refresh_token으로 새 access_token 발급. refresh_token도 갱신됨.",
        request=None,
        responses={
            200: OpenApiResponse(description="토큰 재발급 성공"),
            400: OpenApiResponse(description="refresh 쿠키 없음"),
            403: OpenApiResponse(description="유효하지 않은 토큰"),
        },
    )
    def post(self, request: Request) -> Response:
        #  refresh_token이 없으면 400 에러를 반환.

        valid_refresh_token = request.COOKIES.get("refresh_token")
        if not valid_refresh_token:
            return Response({"error_detail": "refresh_token 쿠키가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 블랙리스트 여부 확인 요청
            if UserLoginService.is_blacklisted(valid_refresh_token):
                return Response(
                    {"error_detail": "로그인 세션이 만료되었습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # 토큰 재발급
            old_refresh = RefreshToken(valid_refresh_token)  # type: ignore[arg-type]
            user_id = old_refresh.payload.get("user_id")
            user = User.objects.get(id=user_id)

            new_access, new_refresh = UserLoginService.generate_token_pair(user)

            UserLoginService.add_to_blacklist(valid_refresh_token)  # 기존 토큰 폐기

        except (TokenError, User.DoesNotExist):
            return Response(
                {"error_detail": "로그인 세션이 만료되었습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 200 성공 응답 (access_token 반환)
        response = Response({"access_token": new_access}, status=status.HTTP_200_OK)
        refresh_lifetime = cast(timedelta, settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"])
        # 쿠키 갱신
        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=True,
            samesite="None",
            path="/",
            max_age=int(refresh_lifetime.total_seconds()),
        )
        return response
