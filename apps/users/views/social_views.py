from __future__ import annotations

import logging
import secrets
from typing import Any, Callable

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.users.services.kakao import KakaoOAuthService
from apps.users.services.naver import NaverOAuthService
from apps.users.services.social_auth import SocialAuthError
from apps.users.services.social_login_service import SocialLoginService
from apps.users.utils.social_auth_help import get_frontend_url, set_refresh_cookie

logger = logging.getLogger(__name__)

# state가 필요한 provider 목록
_STATE_PROVIDERS = {"naver"}

# provider → 인증 URL 빌더 매핑
_AUTH_URL_BUILDERS: dict[str, Callable[[str | None], str]] = {
    "kakao": lambda state: KakaoOAuthService.get_auth_url(),
    "naver": lambda state: NaverOAuthService.get_auth_url(state),
}


@extend_schema(
    tags=["소셜 로그인"],
    summary="소셜 로그인 (카카오 / 네이버)",
    parameters=[
        OpenApiParameter(
            name="provider", location="path", description="소셜 provider (kakao | naver)", required=True, type=str
        ),
    ],
    responses={302: None},
)
class SocialLoginView(APIView):
    """소셜 OAuth 인증 페이지로 302 리다이렉트"""

    permission_classes = [AllowAny]

    def get(self, request: Request, provider: str) -> HttpResponseRedirect:
        if provider not in _AUTH_URL_BUILDERS:
            return redirect(get_frontend_url("/social-callback", provider=provider, is_success="false"))

        state = None
        if provider in _STATE_PROVIDERS:
            state = secrets.token_urlsafe(16)
            request.session[f"{provider}_oauth_state"] = state  # CSRF 방지용 세션 저장

        return redirect(_AUTH_URL_BUILDERS[provider](state))


@extend_schema(
    tags=["소셜 로그인"],
    summary="소셜 로그인 콜백 (카카오 / 네이버)",
    parameters=[
        OpenApiParameter(
            name="provider", location="path", description="소셜 provider (kakao | naver)", required=True, type=str
        ),
        OpenApiParameter(name="code", description="OAuth 인가 코드", required=True, type=str),
        OpenApiParameter(name="state", description="CSRF 방지 state (네이버 전용)", required=False, type=str),
        OpenApiParameter(name="error", description="OAuth 오류 코드 (실패 시)", required=False, type=str),
    ],
    responses={302: None},
)
class SocialCallbackView(APIView):
    """소셜 OAuth 콜백 처리 — access 토큰(URL 파라미터) + refresh 토큰(HttpOnly 쿠키) 발급"""

    permission_classes = [AllowAny]

    def get(self, request: Request, provider: str) -> HttpResponseRedirect:
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")

        if error or not code:
            return self._fail(provider)

        # state 검증 (CSRF) — state가 필요한 provider만 검사
        if provider in _STATE_PROVIDERS:
            expected_state = request.session.pop(f"{provider}_oauth_state", None)
            if not expected_state or state != expected_state:
                logger.warning("%s OAuth state 불일치 (CSRF 의심)", provider)
                return self._fail(provider)

        try:
            result = SocialLoginService.login(provider, code, state)
        except SocialAuthError:
            logger.exception("%s 로그인 실패", provider)
            return self._fail(provider)

        return self._success(provider, result)

    def _success(self, provider: str, result: dict[str, Any]) -> HttpResponseRedirect:
        # access 토큰 → URL 파라미터 (토큰 형식)
        # refresh 토큰 → HttpOnly 쿠키
        response = redirect(
            get_frontend_url(
                "/social-callback",
                provider=provider,
                is_success="true",
                access_token=result["access"],
            )
        )
        set_refresh_cookie(response, result["refresh"])
        return response

    def _fail(self, provider: str) -> HttpResponseRedirect:
        return redirect(get_frontend_url("/social-callback", provider=provider, is_success="false"))
