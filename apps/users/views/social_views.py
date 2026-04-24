from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services.social_auth import SocialAuthError, SocialAuthService


def set_auth_cookies(response: Any, refresh: str) -> None:
    response.set_cookie(
        "refresh_token",
        refresh,
        max_age=60 * 60 * 24 * 4,  # 4일
        domain=getattr(settings, "COOKIE_DOMAIN", None),
        httponly=True,
        secure=getattr(settings, "COOKIE_SECURE", False),
        samesite="Lax",
        path="/",
    )


class SocialLoginView(APIView):
    """
    소셜 로그인 뷰
    카카오 또는 네이버 OAuth 인증 페이지로 302 리다이렉트
    """

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request: HttpRequest, provider: str) -> HttpResponse:
        try:
            auth_url = SocialAuthService.get_auth_url(provider)
        except SocialAuthError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return redirect(auth_url)


class SocialCallbackView(APIView):
    """
    소셜 로그인 콜백 뷰
    OAuth 인가 코드를 받아 로그인 또는 회원가입 처리 후 JWT 반환
    - 기존 소셜 유저       : 로그인 후 토큰 발급
    - 일반 이메일 가입 유저 : 400 에러 반환
    - 신규 유저            : 회원가입 후 토큰 발급
    """

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request: HttpRequest, provider: str) -> HttpResponse:
        if request.GET.get("error"):
            return Response({"detail": request.GET["error"]}, status=status.HTTP_400_BAD_REQUEST)

        code: str | None = request.GET.get("code")
        if not code:
            return Response({"detail": "인가 코드(code)가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = SocialAuthService.login(
                provider=provider,
                code=code,
                state=request.GET.get("state", ""),
            )
        except SocialAuthError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "서버 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = Response(
            {"is_new_user": result["is_new_user"], "access": result["access"]},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, result["refresh"])
        return response
