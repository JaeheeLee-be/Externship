from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services.social_auth import SocialAuthService
from apps.users.utils.social_exceptions import InternalServerError, SocialAuthError


def set_auth_cookies(response: Any, refresh: str) -> None:
    response.set_cookie(
        "refresh_token",
        refresh,
        max_age=60 * 60 * 24 * 4,  # 4일
        domain=getattr(settings, "COOKIE_DOMAIN", None),
        httponly=True,
        secure=getattr(settings, "COOKIE_SECURE", True),
        samesite=getattr(settings, "COOKIE_SAMESITE", "Lax"),
        path="/",
    )


class SocialLoginView(APIView):
    """
    소셜 로그인 뷰
    카카오 또는 네이버 OAuth 인증 페이지로 302 리다이렉트
    """

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    def get(self, request: HttpRequest, provider: str) -> HttpResponse:
        try:
            auth_url = SocialAuthService.get_auth_url(provider)
        except SocialAuthError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return redirect(auth_url)


class SocialCallbackView(APIView):
    """
    소셜 로그인 콜백 뷰
    OAuth 인가 코드를 받아 로그인 또는 회원가입 처리 후 프론트엔드로 302 리다이렉트
    - 성공 : access token을 쿼리 파라미터로, refresh token을 HttpOnly 쿠키로 전달
    - 실패 : error 메세지를 쿼리 파라미터로 전달
    """

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    def get(self, request: HttpRequest, provider: str) -> HttpResponse:
        frontend_url: str = settings.FRONTEND_REDIRECT_URI

        try:
            result = SocialAuthService.process_user(
                provider=provider,
                code=request.GET.get("code", ""),
                state=request.GET.get("state", ""),
                error=request.GET.get("error"),
            )
        except SocialAuthError as e:
            return redirect(f"{frontend_url}?{urlencode({'error': str(e)})}")
        except Exception:
            return redirect(f"{frontend_url}?{urlencode({'error': str(InternalServerError())})}")

        params = urlencode({"access": result["access"], "is_new_user": str(result["is_new_user"]).lower()})
        response = redirect(f"{frontend_url}?{params}")
        set_auth_cookies(response, result["refresh"])
        return response
