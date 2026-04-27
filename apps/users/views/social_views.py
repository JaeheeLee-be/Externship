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
from apps.users.utils.social_exceptions import SocialAuthError


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

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    def get(self, request: HttpRequest, provider: str) -> HttpResponse:
        try:
            auth_url = SocialAuthService.get_auth_url(provider)
        except SocialAuthError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return redirect(auth_url)


class SocialCallbackView(APIView):

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = []

    def get(self, request: HttpRequest, provider: str) -> HttpResponse:
        frontend_url: str = getattr(settings, "FRONTEND_REDIRECT_URI", "")

        try:
            result = SocialAuthService.process_user(
                provider=provider,
                code=request.GET.get("code", ""),
                state=request.GET.get("state", ""),
                error=request.GET.get("error"),
            )
        except SocialAuthError as e:
            params = urlencode(
                {
                    "provider": provider,
                    "is_success": "false",
                }
            )
            return redirect(f"{frontend_url}/social-callback?{params}")

        params = urlencode(
            {"provider": provider, "is_success": "true", "is_new_user": str(result["is_new_user"]).lower()}
        )
        response = redirect(f"{frontend_url}/social-callback?{params}")
        set_auth_cookies(response, result["refresh"])
        return response
